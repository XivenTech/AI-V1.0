import asyncio
import logging
from typing import Dict
from app.core.config import settings
from app.database.session import SessionLocal
from app.models.call import CallRecord
from app.state_machine.notification import NotificationState

logger = logging.getLogger(__name__)


class NotificationScheduler:
    """外呼超时监听与智能升级调度器"""

    def __init__(self):
        self._watchdog_tasks: Dict[int, asyncio.Task] = {}

    def schedule_call_timeout_watchdog(self, call_record_id: int, timeout_seconds: int = 25):
        """为外呼记录挂载超时守护协程"""
        task = asyncio.create_task(self._watchdog_worker(call_record_id, timeout_seconds))
        self._watchdog_tasks[call_record_id] = task

    async def _watchdog_worker(self, call_record_id: int, timeout_seconds: int):
        try:
            await asyncio.sleep(timeout_seconds)
            db = SessionLocal()
            try:
                record = db.get(CallRecord, call_record_id)
                if record and record.status == NotificationState.CALLING.value:
                    logger.info(f"【呼叫超时守护】外呼记录 #{call_record_id} ({record.contact_name}) 已超 {timeout_seconds}s 未接听，触发超时升级")
                    from app.services.call.service import call_service
                    await call_service.handle_call_timeout_or_reject(db, call_record_id, is_timeout=True)
            finally:
                db.close()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"呼叫超时守护协程异常: {e}")
        finally:
            self._watchdog_tasks.pop(call_record_id, None)

    def cancel_watchdog(self, call_record_id: int):
        task = self._watchdog_tasks.pop(call_record_id, None)
        if task and not task.done():
            task.cancel()


notification_scheduler = NotificationScheduler()
