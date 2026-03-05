from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from ..database import Base


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    device_uid = Column(String, unique=True, index=True, nullable=False)  # BLE MAC or serial
    name = Column(String, nullable=False, default="Capteur")
    firmware_version = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    last_seen = Column(DateTime, nullable=True)
    battery_level = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # One device belongs to one wearer
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="device")

    measurements = relationship("Measurement", back_populates="device", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="device", cascade="all, delete-orphan")
