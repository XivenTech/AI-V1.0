import uuid
import logging
from datetime import datetime
from typing import Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.alarm import Alarm
from app.models.workorder import WorkOrder
from app.state_machine.workorder import WorkOrderStateMachine, WorkOrderState
from app.websocket.manager import websocket_manager

logger = logging.getLogger(__name__)


class WorkOrderService:
    """智能维修工单服务"""

    async def auto_create_order_from_alarm(
        self,
        session: Session,
        alarm_id: int,
        assignee: str = "值班工程师"
    ) -> WorkOrder:
        """
        电话接听闭环后，自动从报警生成智能维修工单
        """
        alarm = session.get(Alarm, alarm_id)
        if not alarm:
            raise ValueError(f"报警不存在: #{alarm_id}")

        # 检查是否已存在工单
        existing = session.execute(
            select(WorkOrder).where(WorkOrder.alarm_id == alarm_id)
        ).scalars().first()
        if existing:
            logger.info(f"报警 #{alarm_id} 已存在关联工单 #{existing.order_code}")
            return existing

        date_prefix = datetime.now().strftime("%Y%m%d")
        order_code = f"WO-{date_prefix}-{uuid.uuid4().hex[:6].upper()}"

        # 关联 AI 分析结果
        ai_suggestion = "建议停机断电排查核心执行元件与回路截止阀状态。"
        steps = [
            "现场安全警示隔离与停电挂牌",
            "排查机械液压泄漏点与油温异常",
            "修复关键阀件密封面或紧固松脱电气接线",
            "加压试机测试并复核运行指标"
        ]

        if alarm.ai_analysis:
            ai_suggestion = alarm.ai_analysis.suggestion
            if alarm.ai_analysis.checklist:
                steps = alarm.ai_analysis.checklist

        work_order = WorkOrder(
            order_code=order_code,
            alarm_id=alarm.id,
            title=f"【自动派单】{alarm.title} 现场处置单",
            priority=alarm.level,
            status=WorkOrderState.PENDING.value,
            assignee=assignee,
            description=f"故障描述: {alarm.message} (触发值: {alarm.trigger_value} {alarm.unit}, 阈值: {alarm.threshold} {alarm.unit})",
            ai_suggestion=ai_suggestion,
            steps=steps,
            solution_note=""
        )
        session.add(work_order)
        session.commit()
        session.refresh(work_order)

        logger.info(f"【智能工单生成】成功为报警 #{alarm.id} 创建工单 #{work_order.order_code}，指派人: {assignee}")

        # 广播 WebSocket
        await websocket_manager.broadcast(
            "workorder_created",
            {
                "workorder_id": work_order.id,
                "order_code": work_order.order_code,
                "alarm_id": alarm.id,
                "title": work_order.title,
                "priority": work_order.priority,
                "status": work_order.status,
                "assignee": work_order.assignee,
                "ai_suggestion": work_order.ai_suggestion,
                "steps": work_order.steps,
                "created_at": work_order.created_at.isoformat()
            }
        )

        return work_order

    async def transition_order(
        self,
        session: Session,
        order_id: int,
        target_state: str,
        operator: str = "OPERATOR",
        solution_note: str = ""
    ) -> WorkOrder:
        """
        工单状态机流转
        """
        order = session.get(WorkOrder, order_id)
        if not order:
            raise ValueError(f"工单不存在: #{order_id}")

        return WorkOrderStateMachine.transition(
            session=session,
            workorder=order,
            target_state=target_state,
            operator=operator,
            solution_note=solution_note
        )


workorder_service = WorkOrderService()
