from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class GasReadings(BaseModel):
    hcn: Optional[float] = None
    h2s: Optional[float] = None
    co: Optional[float] = None
    ch2o: Optional[float] = None
    c3h4o: Optional[float] = None
    voc: Optional[float] = None


class GatewayPayload(BaseModel):
    """Legacy single-measurement payload sent by a BLE gateway."""
    device_uid: str
    gateway_id: str
    timestamp: Optional[datetime] = None
    measurements: GasReadings
    battery_level: Optional[float] = None
    signal_strength: Optional[float] = None


# ── File-format schemas (matches the JSON files produced by gateways) ──────────

class GatewayFileMeasurement(BaseModel):
    hcn: Optional[float] = None
    h2s: Optional[float] = None
    co: Optional[float] = None
    ch2o: Optional[float] = None
    c3h4o: Optional[float] = None
    voc: Optional[float] = None


class GatewayFileLog(BaseModel):
    timestamp: datetime
    level: str      # "err" | "wrn" | "inf" | "dbg"
    message: str


class GatewayFileEntry(BaseModel):
    """One device block inside a gateway JSON file."""
    gateway_id: str
    user_id: str            # maps to User.user_uid
    device_id: str          # maps to Device.device_uid
    battery_lvl: Optional[float] = None
    start_timestamp: datetime
    interval_sec: int
    measurements: List[GatewayFileMeasurement]
    logs: List[GatewayFileLog] = []


# ── Output schemas ──────────────────────────────────────────────────────────────

class MeasurementOut(BaseModel):
    id: int
    device_id: int
    timestamp: datetime
    hcn: Optional[float] = None
    h2s: Optional[float] = None
    co: Optional[float] = None
    ch2o: Optional[float] = None
    c3h4o: Optional[float] = None
    voc: Optional[float] = None
    battery_level: Optional[float] = None
    signal_strength: Optional[float] = None
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
