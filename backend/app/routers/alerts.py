from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.alert import Alert, GasThreshold
from ..models.device import Device
from ..models.user import User, UserRole
from ..schemas.alert import AlertOut, AlertAcknowledge, ThresholdOut, ThresholdUpdate
from ..core.security import get_current_user, require_role
from ..services.ai_service import DEFAULT_THRESHOLDS

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/", response_model=List[AlertOut])
def get_alerts(
    wearer_id: Optional[int] = Query(None),
    unacknowledged_only: bool = Query(False),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Alert)

    if current_user.role == UserRole.wearer:
        device = db.query(Device).filter(Device.user_id == current_user.id).first()
        if not device:
            return []
        query = query.filter(Alert.device_id == device.id)
    elif current_user.role == UserRole.doctor:
        patient_ids = [p.id for p in current_user.patients]
        devices = db.query(Device).filter(Device.user_id.in_(patient_ids)).all()
        query = query.filter(Alert.device_id.in_([d.id for d in devices]))
        if wearer_id:
            d = db.query(Device).filter(Device.user_id == wearer_id).first()
            if d:
                query = query.filter(Alert.device_id == d.id)
    else:  # supervisor
        if wearer_id:
            d = db.query(Device).filter(Device.user_id == wearer_id).first()
            if d:
                query = query.filter(Alert.device_id == d.id)

    if unacknowledged_only:
        query = query.filter(Alert.acknowledged == False)

    return query.order_by(Alert.timestamp.desc()).limit(limit).all()


@router.patch("/{alert_id}/acknowledge", response_model=AlertOut)
def acknowledge_alert(
    alert_id: int,
    body: AlertAcknowledge,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alerte introuvable")
    alert.acknowledged = body.acknowledged
    alert.acknowledged_by = current_user.id
    alert.acknowledged_at = datetime.utcnow()
    db.commit()
    db.refresh(alert)
    return alert


@router.get("/thresholds", response_model=List[ThresholdOut])
def get_thresholds(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    thresholds = db.query(GasThreshold).all()
    return thresholds


@router.patch("/thresholds/{gas_type}", response_model=ThresholdOut)
def update_threshold(
    gas_type: str,
    update: ThresholdUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.supervisor)),
):
    t = db.query(GasThreshold).filter(GasThreshold.gas_type == gas_type).first()
    if not t:
        raise HTTPException(status_code=404, detail="Gaz inconnu")
    t.warning_level = update.warning_level
    t.critical_level = update.critical_level
    db.commit()
    db.refresh(t)
    return t
