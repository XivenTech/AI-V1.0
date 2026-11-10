from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, ConfigDict
from app.schemas.device import DeviceResponse


class AlarmEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    alarm_id: int
    event_type: str
    from_status: str
    to_status: str
    operator: str
    note: str
    created_at: datetime


class AIAnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    alarm_id: int
    root_cause: str
    confidence: float
    risk_level: str
    suggestion: str
    checklist: Optional[List[str]] = None
    created_at: datetime


class AlarmResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: int
    title: str
    level: str
    status: str
    metric_name: str
    trigger_value: float
    threshold: float
    unit: str
    message: str
    ai_analysis_status: str
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None

    device: Optional[DeviceResponse] = None
    ai_analysis: Optional[AIAnalysisResponse] = None


class AlarmTransitionRequest(BaseModel):
    target_state: str  # ACKNOWLEDGED, PROCESSING, RESOLVED, CLOSED
    note: str = ""
    operator: str = "OPERATOR"
