from datetime import datetime
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from ..database import Base


class Measurement(Base):
    """One measurement row = one sample from the device."""
    __tablename__ = "measurements"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # 6 gases (ppm)
    hcn = Column(Float, nullable=True)   # Cyanure d'hydrogène
    h2s = Column(Float, nullable=True)   # Sulfure d'hydrogène
    co = Column(Float, nullable=True)    # Monoxyde de carbone
    ch2o = Column(Float, nullable=True)  # Formaldéhyde
    c3h4o = Column(Float, nullable=True) # Acroléine
    voc = Column(Float, nullable=True)   # Composés organiques volatils

    # Device telemetry
    battery_level = Column(Float, nullable=True)  # %
    signal_strength = Column(Float, nullable=True)  # dBm

    # AI processing results
    risk_score = Column(Float, nullable=True)       # 0-100
    anomaly_detected = Column(Integer, default=0)   # bitmask per gas

    device = relationship("Device", back_populates="measurements")
    alerts = relationship("Alert", back_populates="measurement")


class DeviceLog(Base):
    """Operational log entry sent by a device via the gateway."""
    __tablename__ = "device_logs"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    level = Column(String(10), nullable=False)   # "err", "wrn", "inf", "dbg"
    message = Column(Text, nullable=False)

    device = relationship("Device", back_populates="logs")
