"""
Orchestrates:
  1. Storing a new measurement
  2. Running AI analysis
  3. Persisting alerts
  4. Broadcasting via WebSocket to relevant users
"""
from datetime import datetime
from sqlalchemy.orm import Session
from ..models.device import Device
from ..models.measurement import Measurement
from ..models.alert import Alert, AlertLevel
from ..models.user import User, UserRole, doctor_patient
from ..services.ai_service import run_analysis
from ..core.websocket_manager import manager
from ..schemas.measurement import GatewayPayload


async def process_gateway_payload(payload: GatewayPayload, db: Session) -> Measurement:
    # 1. Resolve device
    device = db.query(Device).filter(Device.device_uid == payload.device_uid).first()
    if not device:
        raise ValueError(f"Device inconnu : {payload.device_uid}")

    # 2. Update device metadata
    device.last_seen = datetime.utcnow()
    if payload.battery_level is not None:
        device.battery_level = payload.battery_level

    # 3. Persist measurement
    m_data = payload.measurements.model_dump()
    measurement = Measurement(
        device_id=device.id,
        timestamp=payload.timestamp or datetime.utcnow(),
        battery_level=payload.battery_level,
        signal_strength=payload.signal_strength,
        log=payload.log,
        **m_data,
    )
    db.add(measurement)
    db.flush()  # get measurement.id without committing

    # 4. Run AI analysis
    analysis = run_analysis(db, measurement)
    measurement.risk_score = analysis["risk_score"]
    measurement.anomaly_detected = analysis["anomaly_detected"]

    # 5. Persist alerts
    created_alerts = []
    for a in analysis["alerts"]:
        alert = Alert(
            device_id=device.id,
            measurement_id=measurement.id,
            gas_type=a["gas_type"],
            value=a["value"],
            threshold=a["threshold"],
            level=AlertLevel(a["level"]),
            message=a["message"],
        )
        db.add(alert)
        created_alerts.append(alert)

    db.commit()
    db.refresh(measurement)

    # 6. Build WebSocket broadcast payload
    ws_payload = {
        "type": "new_measurement",
        "device_uid": device.device_uid,
        "wearer_id": device.user_id,
        "measurement": {
            "id": measurement.id,
            "timestamp": measurement.timestamp.isoformat(),
            "co": measurement.co,
            "co2": measurement.co2,
            "no2": measurement.no2,
            "o3": measurement.o3,
            "voc": measurement.voc,
            "ch4": measurement.ch4,
            "battery_level": measurement.battery_level,
            "risk_score": measurement.risk_score,
            "anomaly_detected": measurement.anomaly_detected,
        },
        "alerts": [
            {"gas_type": a.gas_type, "level": a.level, "message": a.message}
            for a in created_alerts
        ],
        "trends": analysis["trends"],
        "recommendations": analysis["recommendations"],
    }

    # Notify the wearer
    await manager.send_to_user(device.user_id, ws_payload)

    # Notify doctors following this patient
    doctor_rows = db.execute(
        doctor_patient.select().where(doctor_patient.c.patient_id == device.user_id)
    ).fetchall()
    for row in doctor_rows:
        await manager.send_to_user(row.doctor_id, ws_payload)

    # Notify supervisor(s)
    wearer = db.query(User).filter(User.id == device.user_id).first()
    if wearer and wearer.supervisor_id:
        await manager.send_to_user(wearer.supervisor_id, ws_payload)

    return measurement
