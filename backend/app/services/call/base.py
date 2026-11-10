from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class CallResult(BaseModel):
    """统一标准化外呼调用返回结构"""
    success: bool = Field(..., description="外呼请求是否成功发起")
    call_id: str = Field(..., description="供应商返回的唯一呼叫任务ID或本地业务ID")
    message: str = Field(default="", description="结果描述或失败原因")
    provider: str = Field(..., description="使用的外呼服务商代码，如 aliyun, mock")
    raw_response: Dict[str, Any] = Field(default_factory=dict, description="供应商原始响应报文")


class BaseCallProvider(ABC):
    """外呼供应商抽象基类（适配器模式）"""

    @abstractmethod
    async def make_call(
        self,
        phone: str,
        template_code: str,
        template_param: Optional[Dict[str, Any]] = None
    ) -> CallResult:
        """
        发起语音通知外呼
        :param phone: 被叫真实手机号码 (E.164 或 11位国内手机号)
        :param template_code: 语音通知模板代号 (如 TTS_xxxx)
        :param template_param: 模板插值变量字典，如 {"device": "主液压泵", "level": "P1", "pressure": "12.5"}
        """
        pass

    @abstractmethod
    async def query_call_status(self, call_id: str) -> Dict[str, Any]:
        """查询呼叫状态与通话详情"""
        pass
