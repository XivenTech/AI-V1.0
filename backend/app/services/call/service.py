import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.alarm import Alarm
from app.models.contact import Contact
from app.models.call import CallRecord
from app.state_machine.alarm import AlarmStateMachine, AlarmState
from app.state_machine.notification import NotificationStateMachine, NotificationState
from app.services.call.base import BaseCallProvider, CallResult
from app.services.call.aliyun_provider import AliyunCallProvider
from app.services.call.mock_provider import MockCallProvider
from app.websocket.manager import websocket_manager

logger = logging.getLogger(__name__)


class CallService:
    """呼叫调度聚合服务"""

    def __init__(self):
        self.aliyun_provider = AliyunCallProvider()
        self.mock_provider = MockCallProvider()
        self.current_provider_name = settings.CALL_PROVIDER

    def get_provider(self, provider_override: Optional[str] = None) -> BaseCallProvider:
        p_name = provider_override or self.current_provider_name
        if p_name.lower() == "aliyun":
            # 如果配置了 aliyun 但没有填写 AK，则打日志并使用 aliyun_provider（其内部有安全保护），
            # 同时也方便用户在配置真实 AK 后立即生效
            return self.aliyun_provider
        return self.mock_provider

    def set_active_provider(self, provider_name: str):
        """支持现场动态切换线路通道"""
        if provider_name in ("aliyun", "mock"):
            self.current_provider_name = provider_name
            logger.info(f"【呼叫线路切换】当前外呼服务通道已切换为: {provider_name}")

    async def initiate_alarm_call(
        self,
        session: Session,
        alarm_id: int,
        priority: int = 1,
        provider_name: Optional[str] = None
    ) -> CallRecord:
        """
        根据优先级调度联系人并发起外呼
        """
        alarm = session.get(Alarm, alarm_id)
        if not alarm:
            raise ValueError(f"报警不存在: #{alarm_id}")

        # 获取对应优先级的有效联系人
        stmt = select(Contact).where(Contact.priority == priority, Contact.is_active == True)
        contact = session.execute(stmt).scalars().first()

        if not contact:
            # 降级：如果找不到对应 priority，选任意有效联系人
            contact = session.execute(select(Contact).where(Contact.is_active == True)).scalars().first()

        contact_name = contact.name if contact else f"值班人-优先级{priority}"
        contact_phone = contact.phone if contact else "13800000000"

        # 构造呼叫记录
        selected_provider_code = provider_name or self.current_provider_name
        call_record = CallRecord(
            alarm_id=alarm.id,
            contact_name=contact_name,
            contact_phone=contact_phone,
            priority=priority,
            provider=selected_provider_code,
            status=NotificationState.CALLING.value,
            duration=0,
            template_code=settings.TTS_CODE,
            template_params={
                "device": alarm.device.name if alarm.device else "核心工业设备",
                "level": alarm.level,
                "metric": alarm.metric_name,
                "value": str(alarm.trigger_value),
                "threshold": str(alarm.threshold),
                "time": datetime.now().strftime("%H:%M:%S")
            }
        )
        session.add(call_record)
        session.commit()
        session.refresh(call_record)

        logger.info(
            f"【呼叫调度】启动第 {priority} 轮外呼: 准备呼叫 [{contact_name} ({contact_phone})], "
            f"使用通道: [{selected_provider_code}], 报警: #{alarm.id}"
        )

        # 广播 WebSocket 呼叫状态
        await websocket_manager.broadcast(
            "call_status",
            {
                "call_record_id": call_record.id,
                "alarm_id": alarm.id,
                "contact_name": contact_name,
                "contact_phone": contact_phone,
                "priority": priority,
                "provider": selected_provider_code,
                "status": "CALLING",
                "note": f"正在向第 {priority} 联系人 {contact_name} 发起语音外呼..."
            }
        )

        # 实际调用 Provider 发起外呼
        provider = self.get_provider(selected_provider_code)
        call_result: CallResult = await provider.make_call(
            phone=contact_phone,
            template_code=settings.TTS_CODE,
            template_param=call_record.template_params
        )

        call_record.call_id = call_result.call_id or f"temp-{call_record.id}"
        if not call_result.success:
            call_record.error_msg = call_result.message
            if selected_provider_code == "aliyun":
                logger.warning(f"阿里云真实呼叫下发未成功: {call_result.message}，保留记录供排查")
        else:
            call_record.error_msg = ""

        session.commit()
        session.refresh(call_record)

        # 挂载超时自动升级守护协程
        from app.services.notification.scheduler import notification_scheduler
        notification_scheduler.schedule_call_timeout_watchdog(call_record.id, settings.CALL_TIMEOUT_SECONDS)

        return call_record

    async def handle_call_answered(
        self,
        session: Session,
        call_record_id: int,
        duration: int = 28
    ) -> CallRecord:
        """
        处理呼叫被接听事件
        - 状态机流转为 ANSWERED
        - 报警状态机流转为 ACKNOWLEDGED
        - 自动创建维修工单 WorkOrder
        """
        from app.services.notification.scheduler import notification_scheduler
        notification_scheduler.cancel_watchdog(call_record_id)

        call_record = session.get(CallRecord, call_record_id)
        if not call_record:
            raise ValueError(f"呼叫记录不存在: #{call_record_id}")

        call_record.duration = duration
        NotificationStateMachine.transition(
            session=session,
            call_record=call_record,
            target_state=NotificationState.ANSWERED.value,
            note=f"联系人 {call_record.contact_name} 已成功接听电话并听取告警语音（通话时长 {duration} 秒）"
        )

        # 报警状态机更新为 ACKNOWLEDGED
        if call_record.alarm and call_record.alarm.status == AlarmState.TRIGGERED.value:
            AlarmStateMachine.transition(
                session=session,
                alarm=call_record.alarm,
                target_state=AlarmState.ACKNOWLEDGED.value,
                operator=call_record.contact_name,
                note=f"电话语音已送达并由 {call_record.contact_name} 接听确认"
            )

        # 自动闭环创建智能工单
        from app.services.workorder.service import workorder_service
        await workorder_service.auto_create_order_from_alarm(
            session=session,
            alarm_id=call_record.alarm_id,
            assignee=call_record.contact_name
        )

        return call_record

    async def handle_call_timeout_or_reject(
        self,
        session: Session,
        call_record_id: int,
        is_timeout: bool = True
    ) -> Optional[CallRecord]:
        """
        处理未接听或超时事件，触发呼叫升级
        """
        from app.services.notification.scheduler import notification_scheduler
        notification_scheduler.cancel_watchdog(call_record_id)

        call_record = session.get(CallRecord, call_record_id)
        if not call_record:
            return None

        target_state = NotificationState.UNANSWERED.value if is_timeout else NotificationState.REJECTED.value
        note_text = "超时未接听" if is_timeout else "用户拒接/正忙"

        NotificationStateMachine.transition(
            session=session,
            call_record=call_record,
            target_state=target_state,
            note=f"{call_record.contact_name} {note_text}"
        )

        # 判定是否需要升级（如果当前是第一联系人，立即升级呼叫第二联系人）
        if call_record.priority == 1:
            NotificationStateMachine.transition(
                session=session,
                call_record=call_record,
                target_state=NotificationState.ESCALATED.value,
                note="第一联系人未接听，已触发自动升级流程"
            )

            # 记录报警事件
            if call_record.alarm:
                from app.models.alarm_event import AlarmEvent
                event = AlarmEvent(
                    alarm_id=call_record.alarm_id,
                    event_type="CALL_ESCALATED",
                    from_status=call_record.alarm.status,
                    to_status=call_record.alarm.status,
                    operator="SYSTEM",
                    note=f"第一联系人 [{call_record.contact_name}] 呼叫未通，系统自动升级拨打第二联系人"
                )
                session.add(event)
                session.commit()

            # 启动第二联系人拨打
            new_call = await self.initiate_alarm_call(
                session=session,
                alarm_id=call_record.alarm_id,
                priority=2,
                provider_name=call_record.provider
            )
            return new_call

        return call_record

    async def handle_aliyun_callback(self, session: Session, payload: Dict[str, Any]):
        """
        接收阿里云语音服务 Webhook 回执报文并更新状态机
        """
        call_id = payload.get("call_id") or payload.get("callId")
        status_code = str(payload.get("status_code") or payload.get("statusCode") or "")
        duration = int(payload.get("duration") or 0)

        logger.info(f"【阿里云Webhook回执】收到呼叫回执: call_id={call_id}, status_code={status_code}, duration={duration}")

        if not call_id:
            return

        stmt = select(CallRecord).where(CallRecord.call_id == call_id)
        call_record = session.execute(stmt).scalars().first()
        if not call_record:
            logger.warning(f"未找到对应的 CallRecord: call_id={call_id}")
            return

        call_record.callback_payload = payload

        # 阿里云 status_code 常见值: 200000(接听成功), 200001(未接/超时), 200002(拒接/忙)
        if status_code in ("200000", "SUCCESS", "200") or duration > 0:
            await self.handle_call_answered(session, call_record.id, duration=max(duration, 15))
        elif status_code in ("200001", "TIMEOUT"):
            await self.handle_call_timeout_or_reject(session, call_record.id, is_timeout=True)
        else:
            await self.handle_call_timeout_or_reject(session, call_record.id, is_timeout=False)


call_service = CallService()
