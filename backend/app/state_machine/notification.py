import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Dict, Set, TYPE_CHECKING
from sqlalchemy.orm import Session
from app.websocket.manager import websocket_manager

if TYPE_CHECKING:
    from app.models.call import CallRecord

logger = logging.getLogger(__name__)


class NotificationState(str, Enum):
    IDLE = "IDLE"
    CALLING = "CALLING"
    ANSWERED = "ANSWERED"
    UNANSWERED = "UNANSWERED"
    REJECTED = "REJECTED"
    ESCALATED = "ESCALATED"
    FAILED = "FAILED"


class NotificationStateMachine:
    """呼叫与通知状态机"""

    ALLOWED_TRANSITIONS: Dict[str, Set[str]] = {
        NotificationState.IDLE.value: {
            NotificationState.CALLING.value,
            NotificationState.FAILED.value
        },
        NotificationState.CALLING.value: {
            NotificationState.ANSWERED.value,
            NotificationState.UNANSWERED.value,
            NotificationState.REJECTED.value,
            NotificationState.FAILED.value,
            NotificationState.ESCALATED.value
        },
        NotificationState.UNANSWERED.value: {
            NotificationState.ESCALATED.value,
            NotificationState.CALLING.value
        },
        NotificationState.REJECTED.value: {
            NotificationState.ESCALATED.value,
            NotificationState.CALLING.value
        },
        NotificationState.ESCALATED.value: {
            NotificationState.CALLING.value
        },
        NotificationState.ANSWERED.value: set(),
        NotificationState.FAILED.value: {NotificationState.CALLING.value}
    }

    @classmethod
    def can_transition(cls, from_state: str, to_state: str) -> bool:
        if from_state == to_state:
            return True
        allowed = cls.ALLOWED_TRANSITIONS.get(from_state, set())
        return to_state in allowed

    @classmethod
    def transition(
        cls,
        session: Session,
        call_record: "CallRecord",
        target_state: str,
        note: str = "",
        trigger_hooks: bool = True
    ) -> "CallRecord":
        from_state = call_record.status
        target_state_val = target_state.value if isinstance(target_state, Enum) else target_state

        if from_state == target_state_val:
            return call_record

        if not cls.can_transition(from_state, target_state_val):
            logger.warning(f"通知状态机非法流转警告: {from_state} -> {target_state_val}，强制安全收敛")

        call_record.status = target_state_val
        now = datetime.utcnow()

        if target_state_val == NotificationState.ANSWERED.value:
            if not call_record.answered_at:
                call_record.answered_at = now
        elif target_state_val in (
            NotificationState.UNANSWERED.value,
            NotificationState.REJECTED.value,
            NotificationState.FAILED.value,
            NotificationState.ESCALATED.value
        ):
            if not call_record.ended_at:
                call_record.ended_at = now

        session.commit()
        session.refresh(call_record)

        logger.info(
            f"【呼叫状态机】呼叫记录 #{call_record.id} ({call_record.contact_name} - {call_record.contact_phone}) "
            f"状态流转: [{from_state}] -> [{target_state_val}] (备注: {note})"
        )

        if trigger_hooks:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(
                        websocket_manager.broadcast(
                            "call_status",
                            {
                                "call_record_id": call_record.id,
                                "alarm_id": call_record.alarm_id,
                                "contact_name": call_record.contact_name,
                                "contact_phone": call_record.contact_phone,
                                "priority": call_record.priority,
                                "provider": call_record.provider,
                                "from_status": from_state,
                                "status": target_state_val,
                                "note": note,
                                "duration": call_record.duration
                            }
                        )
                    )
            except Exception as e:
                logger.warning(f"呼叫状态机广播 WebSocket 失败: {e}")

        return call_record


# 挂载到 CallRecord 模型
from app.models.call import CallRecord

def _call_transition(self, session: Session, target_state: str, note: str = ""):
    return NotificationStateMachine.transition(session, self, target_state, note)

CallRecord.transition = _call_transition
