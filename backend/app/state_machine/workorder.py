import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Dict, Set, Optional, TYPE_CHECKING
from sqlalchemy.orm import Session
from app.state_machine.alarm import AlarmStateMachine, AlarmState
from app.websocket.manager import websocket_manager

if TYPE_CHECKING:
    from app.models.workorder import WorkOrder

logger = logging.getLogger(__name__)


class WorkOrderState(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


class WorkOrderStateMachine:
    """智能工单状态机，支持与报警双向闭环联动"""

    ALLOWED_TRANSITIONS: Dict[str, Set[str]] = {
        WorkOrderState.PENDING.value: {
            WorkOrderState.IN_PROGRESS.value,
            WorkOrderState.CANCELLED.value
        },
        WorkOrderState.IN_PROGRESS.value: {
            WorkOrderState.COMPLETED.value,
            WorkOrderState.CANCELLED.value
        },
        WorkOrderState.COMPLETED.value: {
            WorkOrderState.CLOSED.value,
            WorkOrderState.IN_PROGRESS.value  # 重新返修
        },
        WorkOrderState.CLOSED.value: set(),
        WorkOrderState.CANCELLED.value: set()
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
        workorder: "WorkOrder",
        target_state: str,
        operator: str = "OPERATOR",
        solution_note: str = "",
        trigger_hooks: bool = True
    ) -> "WorkOrder":
        from_state = workorder.status
        target_state_val = target_state.value if isinstance(target_state, Enum) else target_state

        if from_state == target_state_val:
            return workorder

        if not cls.can_transition(from_state, target_state_val):
            logger.warning(f"工单状态机警告: {from_state} -> {target_state_val} 不在标准转移矩阵中，安全允许推进")

        workorder.status = target_state_val
        workorder.updated_at = datetime.utcnow()

        if solution_note:
            workorder.solution_note = solution_note

        if target_state_val == WorkOrderState.COMPLETED.value:
            if not workorder.completed_at:
                workorder.completed_at = datetime.utcnow()

        session.commit()
        session.refresh(workorder)

        logger.info(f"【工单状态机】工单 #{workorder.order_code} 状态流转: [{from_state}] -> [{target_state_val}] (操作人: {operator})")

        # 联动报警状态机
        if workorder.alarm:
            if target_state_val == WorkOrderState.IN_PROGRESS.value:
                AlarmStateMachine.transition(
                    session=session,
                    alarm=workorder.alarm,
                    target_state=AlarmState.PROCESSING.value,
                    operator=operator,
                    note=f"关联工单 {workorder.order_code} 已由 {workorder.assignee or operator} 接单处置中"
                )
            elif target_state_val == WorkOrderState.COMPLETED.value:
                AlarmStateMachine.transition(
                    session=session,
                    alarm=workorder.alarm,
                    target_state=AlarmState.RESOLVED.value,
                    operator=operator,
                    note=f"关联工单 {workorder.order_code} 现场维修完成: {solution_note or '故障已消除'}"
                )
            elif target_state_val == WorkOrderState.CLOSED.value:
                AlarmStateMachine.transition(
                    session=session,
                    alarm=workorder.alarm,
                    target_state=AlarmState.CLOSED.value,
                    operator=operator,
                    note=f"工单 {workorder.order_code} 归档闭环，报警恢复正常"
                )

        if trigger_hooks:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(
                        websocket_manager.broadcast(
                            "workorder_update",
                            {
                                "workorder_id": workorder.id,
                                "order_code": workorder.order_code,
                                "alarm_id": workorder.alarm_id,
                                "title": workorder.title,
                                "status": target_state_val,
                                "assignee": workorder.assignee,
                                "solution_note": workorder.solution_note,
                                "updated_at": workorder.updated_at.isoformat()
                            }
                        )
                    )
            except Exception as e:
                logger.warning(f"工单状态机广播 WebSocket 失败: {e}")

        return workorder


# 挂载到 WorkOrder 模型
from app.models.workorder import WorkOrder

def _workorder_transition(self, session: Session, target_state: str, operator: str = "OPERATOR", solution_note: str = ""):
    return WorkOrderStateMachine.transition(session, self, target_state, operator, solution_note)

WorkOrder.transition = _workorder_transition
