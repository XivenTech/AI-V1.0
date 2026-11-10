from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class CallTriggerRequest(BaseModel):
    alarm_id: Optional[int] = None
    phone: str
    contact_name: str = "演示值班人"
    template_code: Optional[str] = None
    template_params: Optional[Dict[str, Any]] = None
    provider: Optional[str] = None  # None表示使用配置默认，可显式指定 aliyun 或 mock


class CallRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    alarm_id: int
    contact_name: str
    contact_phone: str
    priority: int
    provider: str
    call_id: str
    status: str
    duration: int
    template_code: str
    template_params: Optional[Dict[str, Any]] = None
    error_msg: str
    created_at: datetime
    answered_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None


class AliyunCallbackPayload(BaseModel):
    call_id: Optional[str] = None
    call_type: Optional[str] = None
    status_code: Optional[str] = None
    status_msg: Optional[str] = None
    duration: Optional[int] = 0
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    hangup_direction: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None


class CallSimulateRequest(BaseModel):
    call_record_id: Optional[int] = None
    action: str  # ANSWER (模拟接听), TIMEOUT (模拟超时未接听升级), REJECT (模拟拒接)
