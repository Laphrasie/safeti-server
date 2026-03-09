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

    # 6 gases (ppm or ppb depending on gas — stored as raw float)
    hcn = Column(Float, nullable=True)   # Cyanure d'hydrogène (ppm)
    h2s = Column(Float, nullable=True)   # Sulfure d'hydrogène (ppm)
    co = Column(Float, nullable=True)    # Monoxyde de carbone (ppm)
    ch2o = Column(Float, nullable=True)  # formaldéhyde (ppm)
    c3h4o = Column(Float, nullable=True) # Acroléine (ppm)
    voc = Column(Float, nullable=True)   # Volatile Organic Compounds (ppm)

    # Device telemetry
    battery_level = Column(Float, nullable=True)  # %
    signal_strength = Column(Float, nullable=True)  # dBm
    log = Column(Text, nullable=True)

    # AI processing results
    risk_score = Column(Float, nullable=True)       # 0-100
    anomaly_detected = Column(Integer, default=0)   # bitmask per gas

    device = relationship("Device", back_populates="measurements")
    alerts = relationship("Alert", back_populates="measurement")
