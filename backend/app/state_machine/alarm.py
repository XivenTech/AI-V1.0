import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Dict, Set, Optional, TYPE_CHECKING
from sqlalchemy.orm import Session
from app.models.alarm_event import AlarmEvent
from app.websocket.manager import websocket_manager

if TYPE_CHECKING:
    from app.models.alarm import Alarm

logger = logging.getLogger(__name__)


class AlarmState(str, Enum):
    NORMAL = "NORMAL"
    TRIGGERED = "TRIGGERED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    PROCESSING = "PROCESSING"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class InvalidStateTransitionException(Exception):
    def __init__(self, from_state: str, to_state: str, entity: str = "Alarm"):
        super().__init__(f"非法的状态流转：无法将 {entity} 从状态 [{from_state}] 流转至 [{to_state}]")
        self.from_state = from_state
        self.to_state = to_state


class AlarmStateMachine:
    """报警独立状态机，负责状态校验、流转拦截、审计日志记录与业务钩子触发"""

    # 合法转移规则矩阵
    ALLOWED_TRANSITIONS: Dict[str, Set[str]] = {
        AlarmState.NORMAL.value: {AlarmState.TRIGGERED.value},
        AlarmState.TRIGGERED.value: {
            AlarmState.ACKNOWLEDGED.value,
            AlarmState.PROCESSING.value,
            AlarmState.RESOLVED.value,
            AlarmState.CLOSED.value
        },
        AlarmState.ACKNOWLEDGED.value: {
            AlarmState.PROCESSING.value,
            AlarmState.RESOLVED.value,
            AlarmState.CLOSED.value
        },
        AlarmState.PROCESSING.value: {
            AlarmState.RESOLVED.value,
            AlarmState.CLOSED.value
        },
        AlarmState.RESOLVED.value: {
            AlarmState.CLOSED.value,
            AlarmState.TRIGGERED.value  # 再次故障复发
        },
        AlarmState.CLOSED.value: {
            AlarmState.TRIGGERED.value  # 再次触发
        }
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
        alarm: "Alarm",
        target_state: str,
        operator: str = "SYSTEM",
        note: str = "",
        trigger_hooks: bool = True
    ) -> "Alarm":
        """
        触发报警状态流转
        - 校验合法性
        - 更新状态
        - 写入 AlarmEvent 审计
        - 执行事件钩子
        - 广播 WebSocket
        """
        from_state = alarm.status
        target_state_val = target_state.value if isinstance(target_state, Enum) else target_state

        if from_state == target_state_val:
            logger.info(f"报警 #{alarm.id} 状态未变：仍为 {from_state}")
            return alarm

        if not cls.can_transition(from_state, target_state_val):
            raise InvalidStateTransitionException(from_state, target_state_val, entity="Alarm")

        # 1. 更新状态
        alarm.status = target_state_val
        alarm.updated_at = datetime.utcnow()

        if target_state_val in (AlarmState.RESOLVED.value, AlarmState.CLOSED.value):
            if not alarm.resolved_at:
                alarm.resolved_at = datetime.utcnow()

        # 2. 写入审计事件
        event = AlarmEvent(
            alarm_id=alarm.id,
            event_type=f"STATE_{target_state_val}",
            from_status=from_state,
            to_status=target_state_val,
            operator=operator,
            note=note or f"状态机从 {from_state} 流转至 {target_state_val}"
        )
        session.add(event)
        session.commit()
        session.refresh(alarm)

        logger.info(f"【报警状态机】报警 #{alarm.id} ({alarm.title}) 状态成功由 [{from_state}] -> [{target_state_val}] (操作人: {operator})")

        # 3. 异步广播 WebSocket 事件
        if trigger_hooks:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(
                        websocket_manager.broadcast(
                            "alarm_transition",
                            {
                                "alarm_id": alarm.id,
                                "from_status": from_state,
                                "to_status": target_state_val,
                                "operator": operator,
                                "note": note,
                                "updated_at": alarm.updated_at.isoformat()
                            }
                        )
                    )
            except Exception as e:
                logger.warning(f"广播 WebSocket 失败: {e}")

        return alarm


# 扩展 Alarm 模型，使其拥有直接 transition 方法
from app.models.alarm import Alarm

def _alarm_transition(self, session: Session, target_state: str, operator: str = "SYSTEM", note: str = ""):
    return AlarmStateMachine.transition(session, self, target_state, operator, note)

Alarm.transition = _alarm_transition
