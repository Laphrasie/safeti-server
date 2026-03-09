from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.measurement import Measurement
from ..models.device import Device
from ..models.user import User, UserRole
from ..schemas.measurement import MeasurementOut, AIAnalysis, DeviceOut, DeviceCreate
from ..core.security import get_current_user, require_role
from ..services.ai_service import run_analysis, get_thresholds, fetch_recent_values, analyze_trend

router = APIRouter(prefix="/measurements", tags=["measurements"])


def _assert_device_access(device: Device, current_user: User):
    if current_user.role == UserRole.wearer and device.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Accès refusé")
    if current_user.role == UserRole.doctor:
        patient_ids = [p.id for p in current_user.patients]
        if device.user_id not in patient_ids:
            raise HTTPException(status_code=403, detail="Accès refusé")


@router.get("/", response_model=List[MeasurementOut])
def get_measurements(
    device_id: Optional[int] = Query(None),
    wearer_id: Optional[int] = Query(None),
    from_dt: Optional[datetime] = Query(None),
    to_dt: Optional[datetime] = Query(None),
    limit: int = Query(200, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Measurement)

    if current_user.role == UserRole.wearer:
        # Only own measurements
        device = db.query(Device).filter(Device.user_id == current_user.id).first()
        if not device:
            return []
        query = query.filter(Measurement.device_id == device.id)
    elif current_user.role == UserRole.doctor:
        patient_ids = [p.id for p in current_user.patients]
        devices = db.query(Device).filter(Device.user_id.in_(patient_ids)).all()
        device_ids = [d.id for d in devices]
        query = query.filter(Measurement.device_id.in_(device_ids))
        if device_id:
            query = query.filter(Measurement.device_id == device_id)
    else:  # supervisor
        if wearer_id:
            device = db.query(Device).filter(Device.user_id == wearer_id).first()
            if device:
                query = query.filter(Measurement.device_id == device.id)
        elif device_id:
            query = query.filter(Measurement.device_id == device_id)

    if from_dt:
        query = query.filter(Measurement.timestamp >= from_dt)
    if to_dt:
        query = query.filter(Measurement.timestamp <= to_dt)

    return query.order_by(Measurement.timestamp.desc()).limit(limit).all()


@router.get("/latest", response_model=Optional[MeasurementOut])
def get_latest(
    wearer_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    uid = wearer_id if (current_user.role != UserRole.wearer and wearer_id) else current_user.id
    device = db.query(Device).filter(Device.user_id == uid).first()
    if not device:
        return None
    return (
        db.query(Measurement)
        .filter(Measurement.device_id == device.id)
        .order_by(Measurement.timestamp.desc())
        .first()
    )


@router.get("/analysis", response_model=AIAnalysis)
def get_analysis(
    wearer_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return the latest AI analysis for a given wearer."""
    uid = wearer_id if (current_user.role != UserRole.wearer and wearer_id) else current_user.id
    device = db.query(Device).filter(Device.user_id == uid).first()
    if not device:
        raise HTTPException(status_code=404, detail="Aucun capteur trouvé")
    latest = (
        db.query(Measurement)
        .filter(Measurement.device_id == device.id)
        .order_by(Measurement.timestamp.desc())
        .first()
    )
    if not latest:
        raise HTTPException(status_code=404, detail="Aucune mesure disponible")

    thresholds = get_thresholds(db)
    gas_fields = ["hcn", "h2s", "co", "ch2o", "c3h4o", "voc"]
    anomaly_flags = {}
    trends = {}
    recommendations = []

    for gas in gas_fields:
        values = fetch_recent_values(db, device.id, gas)
        trends[gas] = analyze_trend(values) if values else "n/a"
        anomaly_flags[gas] = latest.anomaly_detected is not None and bool(
            latest.anomaly_detected & (1 << gas_fields.index(gas))
        )

    risk = latest.risk_score or 0.0
    if risk >= 80:
        recommendations.append("Quitter immédiatement la zone exposée.")
    elif risk >= 50:
        recommendations.append("Surveiller l'évolution et améliorer la ventilation.")
    if any(anomaly_flags.values()):
        recommendations.append("Des anomalies statistiques ont été détectées.")

    return AIAnalysis(
        risk_score=risk,
        anomaly_flags=anomaly_flags,
        trends=trends,
        recommendations=recommendations,
    )
