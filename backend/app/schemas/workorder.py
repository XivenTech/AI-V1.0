from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class WorkOrderTransitionRequest(BaseModel):
    target_state: str  # IN_PROGRESS, COMPLETED, CLOSED, CANCELLED
    solution_note: str = ""
    operator: str = "OPERATOR"


class WorkOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    order_code: str
    alarm_id: int
    title: str
    priority: str
    status: str
    assignee: str
    description: str
    ai_suggestion: str
    steps: Optional[List[str]] = None
    solution_note: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
