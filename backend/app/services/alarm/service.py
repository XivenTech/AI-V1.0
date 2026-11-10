import asyncio
import logging
from datetime import datetime
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.device import Device
from app.models.alarm import Alarm
from app.models.alarm_event import AlarmEvent
from app.state_machine.alarm import AlarmStateMachine, AlarmState
from app.services.call.service import call_service
from app.services.ai.service import ai_service
from app.websocket.manager import websocket_manager

logger = logging.getLogger(__name__)


class AlarmService:
    """报警核心业务服务"""

    async def trigger_alarm(
        self,
        session: Session,
        device_code: str,
        title: str,
        level: str,
        metric_name: str,
        trigger_value: float,
        threshold: float,
        unit: str,
        message: str
    ) -> Optional[Alarm]:
        """
        触发设备报警：
        1. 幂等排重检查：若同设备同指标已处于活动报警状态，不重复触发
        2. 持久化存储 Alarm 与初始状态机事件
        3. 广播 WebSocket 触发前端大屏红光高亮告警
        4. 【主流程】立即调度真实语音外呼 (第一联系人)
        5. 【异步旁路】非阻塞协程启动 AI 根因推导
        """
        stmt = select(Device).where(Device.code == device_code)
        device = session.execute(stmt).scalars().first()
        if not device:
            logger.warning(f"设备不存在: {device_code}")
            return None

        # 检查是否已有未关闭的活动报警
        active_stmt = select(Alarm).where(
            Alarm.device_id == device.id,
            Alarm.metric_name == metric_name,
            Alarm.status.in_([AlarmState.TRIGGERED.value, AlarmState.ACKNOWLEDGED.value, AlarmState.PROCESSING.value])
        )
        existing_alarm = session.execute(active_stmt).scalars().first()
        if existing_alarm:
            # 持续更新触发值
            existing_alarm.trigger_value = trigger_value
            existing_alarm.updated_at = datetime.utcnow()
            session.commit()
            return existing_alarm

        # 创建新报警
        alarm = Alarm(
            device_id=device.id,
            title=title,
            level=level,
            status=AlarmState.TRIGGERED.value,
            metric_name=metric_name,
            trigger_value=trigger_value,
            threshold=threshold,
            unit=unit,
            message=message,
            ai_analysis_status="PENDING"
        )
        session.add(alarm)
        session.flush()

        # 记录初始流转事件
        event = AlarmEvent(
            alarm_id=alarm.id,
            event_type="TRIGGER",
            from_status=AlarmState.NORMAL.value,
            to_status=AlarmState.TRIGGERED.value,
            operator="ALARM_ENGINE",
            note=f"报警规则触发：{metric_name}={trigger_value}{unit} 越限 (阈值: {threshold}{unit})"
        )
        session.add(event)

        # 更新设备状态为 ALARMING
        device.status = "ALARMING"
        session.commit()
        session.refresh(alarm)

        logger.info(f"【报警中心】产生新告警 #{alarm.id}: [{level}] {title} (设备: {device.name})")

        # 广播报警事件至前端
        await websocket_manager.broadcast(
            "alarm_created",
            {
                "alarm_id": alarm.id,
                "device_id": device.id,
                "device_name": device.name,
                "device_code": device.code,
                "title": alarm.title,
                "level": alarm.level,
                "status": alarm.status,
                "metric_name": alarm.metric_name,
                "trigger_value": alarm.trigger_value,
                "threshold": alarm.threshold,
                "unit": alarm.unit,
                "message": alarm.message,
                "created_at": alarm.created_at.isoformat()
            }
        )

        # ----------------- 核心解耦架构 -----------------
        # 分支 1：【主流程】电话语音通知外呼 (第一优先级联系人张工)
        try:
            await call_service.initiate_alarm_call(session, alarm.id, priority=1)
        except Exception as e:
            logger.error(f"发起电话呼叫异常: {e}")

        # 分支 2：【异步旁路】AI 智能根因分析 (非阻塞后台协程)
        asyncio.create_task(ai_service.analyze_alarm_async(alarm.id))

        return alarm

    async def transition_alarm(
        self,
        session: Session,
        alarm_id: int,
        target_state: str,
        operator: str = "OPERATOR",
        note: str = ""
    ) -> Alarm:
        alarm = session.get(Alarm, alarm_id)
        if not alarm:
            raise ValueError(f"报警不存在: #{alarm_id}")

        return AlarmStateMachine.transition(
            session=session,
            alarm=alarm,
            target_state=target_state,
            operator=operator,
            note=note
        )


alarm_service = AlarmService()
