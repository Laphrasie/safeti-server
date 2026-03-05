from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class GasReadings(BaseModel):
    co: Optional[float] = None
    co2: Optional[float] = None
    no2: Optional[float] = None
    o3: Optional[float] = None
    voc: Optional[float] = None
    ch4: Optional[float] = None


class GatewayPayload(BaseModel):
    """Payload sent by the BLE gateway to the server."""
    device_uid: str
    gateway_id: str
    timestamp: Optional[datetime] = None
    measurements: GasReadings
    battery_level: Optional[float] = None
    signal_strength: Optional[float] = None
    log: Optional[str] = None


class MeasurementOut(BaseModel):
    id: int
    device_id: int
    timestamp: datetime
    co: Optional[float] = None
    co2: Optional[float] = None
    no2: Optional[float] = None
    o3: Optional[float] = None
    voc: Optional[float] = None
    ch4: Optional[float] = None
    battery_level: Optional[float] = None
    signal_strength: Optional[float] = None
    log: Optional[str] = None
    risk_score: Optional[float] = None
    anomaly_detected: Optional[int] = None

    model_config = {"from_attributes": True}


class DeviceOut(BaseModel):
    id: int
    device_uid: str
    name: str
    firmware_version: Optional[str] = None
    is_active: bool
    last_seen: Optional[datetime] = None
    battery_level: Optional[float] = None
    user_id: int

    model_config = {"from_attributes": True}


class DeviceCreate(BaseModel):
    device_uid: str
    name: str
    firmware_version: Optional[str] = None
    user_id: int


class AIAnalysis(BaseModel):
    risk_score: float
    anomaly_flags: dict[str, bool]
    trends: dict[str, str]  # "stable" | "rising" | "falling"
    recommendations: list[str]
