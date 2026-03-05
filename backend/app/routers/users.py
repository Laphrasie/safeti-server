from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.user import User, UserRole, doctor_patient
from ..schemas.user import UserCreate, UserUpdate, UserOut
from ..services.auth_service import create_user
from ..core.security import get_current_user, require_role

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserOut)
def register_user(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.supervisor)),
):
    """Supervisors can create user accounts."""
    return create_user(db, user_in)


@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/", response_model=List[UserOut])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.supervisor, UserRole.doctor)),
):
    if current_user.role == UserRole.supervisor:
        # Return wearers managed by this supervisor
        return db.query(User).filter(User.supervisor_id == current_user.id).all()
    # Doctors: return their patients
    return current_user.patients


@router.get("/{user_id}", response_model=UserOut)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    # Access control
    if current_user.role == UserRole.wearer and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Accès refusé")
    if current_user.role == UserRole.doctor:
        patient_ids = [p.id for p in current_user.patients]
        if user_id not in patient_ids and user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Accès refusé")
    return user


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.supervisor)),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


@router.post("/{doctor_id}/patients/{patient_id}", status_code=201)
def assign_patient(
    doctor_id: int,
    patient_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_role(UserRole.supervisor)),
):
    """Assign a wearer as a patient of a doctor."""
    doctor = db.query(User).filter(User.id == doctor_id, User.role == UserRole.doctor).first()
    patient = db.query(User).filter(User.id == patient_id, User.role == UserRole.wearer).first()
    if not doctor or not patient:
        raise HTTPException(status_code=404, detail="Médecin ou patient introuvable")
    if patient not in doctor.patients:
        doctor.patients.append(patient)
        db.commit()
    return {"detail": "Patient assigné"}
