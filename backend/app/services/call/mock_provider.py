import uuid
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from app.services.call.base import BaseCallProvider, CallResult

logger = logging.getLogger(__name__)


class MockCallProvider(BaseCallProvider):
    """
    测试与离线演示专用呼叫 Provider (备用通道)
    在未配置阿里云 AccessKey 或断网环境下提供 100% 稳定的仿真呼叫体验
    """

    def __init__(self):
        self.active_mock_calls: Dict[str, Dict[str, Any]] = {}

    async def make_call(
        self,
        phone: str,
        template_code: Optional[str] = None,
        template_param: Optional[Dict[str, Any]] = None
    ) -> CallResult:
        call_id = f"mock-call-{uuid.uuid4().hex[:12]}"
        logger.info(f"【Mock呼叫通道】模拟向手机号 [{phone}] 发起语音外呼... 任务ID: {call_id}")

        self.active_mock_calls[call_id] = {
            "call_id": call_id,
            "phone": phone,
            "template_code": template_code or "MOCK_TTS_001",
            "template_param": template_param or {},
            "status": "CALLING",
            "created_at": datetime.utcnow().isoformat()
        }

        return CallResult(
            success=True,
            call_id=call_id,
            message="【模拟呼叫成功】语音通道已接通，正在模拟向目标手机拨打振铃",
            provider="mock",
            raw_response={"mock_status": "RINGING", "call_id": call_id}
        )

    async def query_call_status(self, call_id: str) -> Dict[str, Any]:
        return self.active_mock_calls.get(call_id, {"status": "NOT_FOUND"})
