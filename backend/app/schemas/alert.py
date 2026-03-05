from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from ..models.alert import AlertLevel


class AlertOut(BaseModel):
    id: int
    device_id: int
    measurement_id: Optional[int] = None
    timestamp: datetime
    gas_type: str
    value: Optional[float] = None
    threshold: Optional[float] = None
    level: AlertLevel
    message: str
    acknowledged: bool
    acknowledged_by: Optional[int] = None
    acknowledged_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AlertAcknowledge(BaseModel):
    acknowledged: bool = True


class ThresholdOut(BaseModel):
    id: int
    gas_type: str
    unit: str
    warning_level: float
    critical_level: float

    model_config = {"from_attributes": True}


class ThresholdUpdate(BaseModel):
    warning_level: float
    critical_level: float
