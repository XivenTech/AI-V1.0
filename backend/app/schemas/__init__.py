from app.schemas.device import DeviceResponse, DeviceTelemetry
from app.schemas.alarm import AlarmResponse, AlarmEventResponse, AlarmTransitionRequest, AIAnalysisResponse
from app.schemas.call import CallTriggerRequest, CallRecordResponse, AliyunCallbackPayload, CallSimulateRequest
from app.schemas.contact import ContactUpdate, ContactResponse
from app.schemas.workorder import WorkOrderResponse, WorkOrderTransitionRequest
from app.schemas.demo import ScenarioTriggerRequest, GoldenPathStepResponse

__all__ = [
    "DeviceResponse",
    "DeviceTelemetry",
    "AlarmResponse",
    "AlarmEventResponse",
    "AlarmTransitionRequest",
    "AIAnalysisResponse",
    "CallTriggerRequest",
    "CallRecordResponse",
    "AliyunCallbackPayload",
    "CallSimulateRequest",
    "ContactUpdate",
    "ContactResponse",
    "WorkOrderResponse",
    "WorkOrderTransitionRequest",
    "ScenarioTriggerRequest",
    "GoldenPathStepResponse",
]
