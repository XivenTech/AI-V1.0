from typing import Optional, Dict, Any
from pydantic import BaseModel


class ScenarioTriggerRequest(BaseModel):
    scenario: str  # HYDRAULIC_LEAK, MOTOR_OVERHEAT, DEVICE_OFFLINE, RESET
    device_code: Optional[str] = None
    custom_params: Optional[Dict[str, Any]] = None


class GoldenPathStepResponse(BaseModel):
    step: int
    title: str
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None
