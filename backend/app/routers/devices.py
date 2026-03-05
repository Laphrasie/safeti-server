from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.device import Device
from ..models.user import User, UserRole
from ..schemas.measurement import DeviceOut, DeviceCreate
from ..core.security import get_current_user, require_role

router = APIRouter(prefix="/devices", tags=["devices"])


@router.post("/", response_model=DeviceOut, status_code=201)
def create_device(
    device_in: DeviceCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.supervisor)),
):
    existing = db.query(Device).filter(Device.device_uid == device_in.device_uid).first()
    if existing:
        raise HTTPException(status_code=400, detail="Device UID déjà enregistré")
    device = Device(**device_in.model_dump())
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


@router.get("/", response_model=List[DeviceOut])
def list_devices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.wearer:
        device = db.query(Device).filter(Device.user_id == current_user.id).first()
        return [device] if device else []
    if current_user.role == UserRole.doctor:
        patient_ids = [p.id for p in current_user.patients]
        return db.query(Device).filter(Device.user_id.in_(patient_ids)).all()
    # Supervisor: all devices for their workers
    worker_ids = [w.id for w in current_user.workers]
    return db.query(Device).filter(Device.user_id.in_(worker_ids)).all()


@router.get("/{device_id}", response_model=DeviceOut)
def get_device(
    device_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Capteur introuvable")
    return device
