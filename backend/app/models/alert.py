import enum
from datetime import datetime
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, String, Enum, Boolean
from sqlalchemy.orm import relationship
from ..database import Base


class AlertLevel(str, enum.Enum):
    warning = "warning"
    critical = "critical"
    anomaly = "anomaly"


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    measurement_id = Column(Integer, ForeignKey("measurements.id"), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    gas_type = Column(String, nullable=False)   # co, co2, no2, o3, voc, ch4, risk
    value = Column(Float, nullable=True)
    threshold = Column(Float, nullable=True)
    level = Column(Enum(AlertLevel), nullable=False)
    message = Column(String, nullable=False)

    acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)

    device = relationship("Device", back_populates="alerts")
    measurement = relationship("Measurement", back_populates="alerts")


class GasThreshold(Base):
    """Configurable thresholds per gas type."""
    __tablename__ = "gas_thresholds"

    id = Column(Integer, primary_key=True, index=True)
    gas_type = Column(String, unique=True, nullable=False)
    unit = Column(String, nullable=False)
    warning_level = Column(Float, nullable=False)
    critical_level = Column(Float, nullable=False)
