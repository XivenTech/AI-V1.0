from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class DeviceTelemetry(BaseModel):
    device_code: str
    timestamp: datetime
    metrics: Dict[str, Any]
    status: str = "RUNNING"


class DeviceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    type: str
    location: str
    status: str
    metrics: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
