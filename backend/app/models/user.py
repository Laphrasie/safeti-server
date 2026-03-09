import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Enum, DateTime, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship, backref
from ..database import Base

# Association table: doctor <-> patient (wearer)
doctor_patient = Table(
    "doctor_patient",
    Base.metadata,
    Column("doctor_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("patient_id", Integer, ForeignKey("users.id"), primary_key=True),
)


class UserRole(str, enum.Enum):
    wearer = "wearer"
    doctor = "doctor"
    supervisor = "supervisor"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    role = Column(Enum(UserRole), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # External string UID used by gateways (e.g. "aez321e35az1")
    user_uid = Column(String, unique=True, nullable=True, index=True)

    # For wearers: supervisor_id points to their supervisor
    supervisor_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    device = relationship("Device", back_populates="user", uselist=False)

    # Supervisor -> list of wearers they manage
    workers = relationship(
        "User",
        foreign_keys=[supervisor_id],
        backref=backref("supervisor_rel", remote_side=[id]),
    )

    # Doctor <-> patients (many-to-many)
    patients = relationship(
        "User",
        secondary=doctor_patient,
        primaryjoin="User.id == doctor_patient.c.doctor_id",
        secondaryjoin="User.id == doctor_patient.c.patient_id",
        backref="doctors",
    )
