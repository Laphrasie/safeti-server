"""
Orchestrates:
  1. Storing new measurements
  2. Running AI analysis
  3. Persisting alerts
  4. Broadcasting via WebSocket to relevant users
"""
from datetime import datetime, timedelta
from typing import List
from sqlalchemy.orm import Session
from ..models.device import Device
from ..models.measurement import Measurement, DeviceLog
from ..models.alert import Alert, AlertLevel
from ..models.user import User, doctor_patient
from ..services.ai_service import run_analysis
from ..core.websocket_manager import manager
from ..schemas.measurement import GatewayPayload, GatewayFileEntry


async def _broadcast(device: Device, measurement: Measurement, analysis: dict,
                     created_alerts: list, db: Session):
    """Send a WebSocket notification to the wearer, their doctors and supervisor."""
    ws_payload = {
        "type": "new_measurement",
        "device_uid": device.device_uid,
        "wearer_id": device.user_id,
        "measurement": {
            "id": measurement.id,
            "timestamp": measurement.timestamp.isoformat(),
            "hcn": measurement.hcn,
            "h2s": measurement.h2s,
            "co": measurement.co,
            "ch2o": measurement.ch2o,
            "c3h4o": measurement.c3h4o,
            "voc": measurement.voc,
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

    await manager.send_to_user(device.user_id, ws_payload)

    doctor_rows = db.execute(
        doctor_patient.select().where(doctor_patient.c.patient_id == device.user_id)
    ).fetchall()
    for row in doctor_rows:
        await manager.send_to_user(row.doctor_id, ws_payload)

    wearer = db.query(User).filter(User.id == device.user_id).first()
    if wearer and wearer.supervisor_id:
        await manager.send_to_user(wearer.supervisor_id, ws_payload)


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
        **m_data,
    )
    db.add(measurement)
    db.flush()

    # 4. AI analysis
    analysis = run_analysis(db, measurement)
    measurement.risk_score = analysis["risk_score"]
    measurement.anomaly_detected = analysis["anomaly_detected"]

    # 5. Alerts
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

    await _broadcast(device, measurement, analysis, created_alerts, db)
    return measurement


async def process_gateway_file(entries: List[GatewayFileEntry], db: Session) -> dict:
    """
    Process a batch of device entries from a gateway JSON file.
    - Looks up the user by user_uid; prints a warning and skips if not found.
    - Auto-creates the device if it doesn't exist yet.
    - Creates one Measurement row per sample (timestamp = start + i * interval_sec).
    - Creates DeviceLog rows for each log entry.
    - Runs AI analysis and persists alerts for the last measurement of each device.
    """
    total_measurements = 0
    total_logs = 0
    skipped_entries = []

    for entry in entries:
        # Resolve user by external string UID
        user = db.query(User).filter(User.user_uid == entry.user_id).first()
        if not user:
            print(
                f"[ingest-file] WARN: user_uid '{entry.user_id}' introuvable dans la DB "
                f"(gateway={entry.gateway_id}, device={entry.device_id}) — entrée ignorée."
            )
            skipped_entries.append(entry.device_id)
            continue

        # Find or create device
        device = db.query(Device).filter(Device.device_uid == entry.device_id).first()
        if not device:
            device = Device(
                device_uid=entry.device_id,
                name=f"Capteur {entry.device_id}",
                user_id=user.id,
            )
            db.add(device)
            db.flush()

        # Update device metadata
        device.last_seen = datetime.utcnow()
        if entry.battery_lvl is not None:
            device.battery_level = entry.battery_lvl

        # Persist measurements
        last_measurement = None
        last_analysis = None
        last_alerts = []

        for i, sample in enumerate(entry.measurements):
            ts = entry.start_timestamp + timedelta(seconds=i * entry.interval_sec)
            measurement = Measurement(
                device_id=device.id,
                timestamp=ts,
                battery_level=entry.battery_lvl,
                **sample.model_dump(),
            )
            db.add(measurement)
            db.flush()

            analysis = run_analysis(db, measurement)
            measurement.risk_score = analysis["risk_score"]
            measurement.anomaly_detected = analysis["anomaly_detected"]

            alerts = []
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
                alerts.append(alert)

            last_measurement = measurement
            last_analysis = analysis
            last_alerts = alerts
            total_measurements += 1

        # Persist device logs
        for log_entry in entry.logs:
            db.add(DeviceLog(
                device_id=device.id,
                timestamp=log_entry.timestamp,
                level=log_entry.level,
                message=log_entry.message,
            ))
            total_logs += 1

        db.commit()

        # Broadcast only the last measurement to avoid flooding
        if last_measurement and last_analysis is not None:
            db.refresh(last_measurement)
            await _broadcast(device, last_measurement, last_analysis, last_alerts, db)

    return {
        "measurements_created": total_measurements,
        "logs_created": total_logs,
        "skipped_devices": skipped_entries,
    }
