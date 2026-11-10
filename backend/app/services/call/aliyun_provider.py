import json
import logging
from typing import Dict, Any, Optional
from app.services.call.base import BaseCallProvider, CallResult
from app.core.config import settings

logger = logging.getLogger(__name__)

# 尝试导入阿里云官方 SDK
try:
    from alibabacloud_dyvmsapi20170525.client import Client as DyvmsClient
    from alibabacloud_dyvmsapi20170525 import models as dyvms_models
    from alibabacloud_tea_openapi import models as open_api_models
    from alibabacloud_tea_util import models as util_models
    HAS_ALIYUN_SDK = True
except ImportError:
    HAS_ALIYUN_SDK = False
    logger.warning("阿里云 Dyvmsapi SDK 未安装或不可用")


class AliyunCallProvider(BaseCallProvider):
    """
    阿里云语音服务 (Dyvmsapi) 真实外呼 Provider
    调用 SingleCallByTts 接口，向运维人员真实手机号发起语音告警播报
    """

    def __init__(self):
        self.access_key_id = settings.ALIBABA_CLOUD_ACCESS_KEY_ID.strip()
        self.access_key_secret = settings.ALIBABA_CLOUD_ACCESS_KEY_SECRET.strip()
        self.called_show_number = settings.CALL_CALLED_SHOW_NUMBER.strip()
        self.default_tts_code = settings.TTS_CODE.strip()
        self.client = None

        if HAS_ALIYUN_SDK and self.access_key_id and self.access_key_secret:
            try:
                config = open_api_models.Config(
                    access_key_id=self.access_key_id,
                    access_key_secret=self.access_key_secret,
                    endpoint="dyvmsapi.aliyuncs.com"
                )
                self.client = DyvmsClient(config)
                logger.info("阿里云语音服务 DyvmsClient 客户端初始化成功")
            except Exception as e:
                logger.error(f"初始化阿里云 DyvmsClient 异常: {e}")
        else:
            logger.info("未检测到有效的阿里云 AK/SK 凭证，系统将提供凭证校验提示与 Mock 自动兜底通道")

    async def make_call(
        self,
        phone: str,
        template_code: Optional[str] = None,
        template_param: Optional[Dict[str, Any]] = None
    ) -> CallResult:
        """
        调用阿里云语音服务进行真实外呼
        """
        target_template = template_code or self.default_tts_code
        params_dict = template_param or {}
        tts_param_str = json.dumps(params_dict, ensure_ascii=False)

        # 检查凭据
        if not self.client:
            msg = (
                "阿里云语音外呼发起失败：未配置有效的 ALIBABA_CLOUD_ACCESS_KEY_ID 或 SDK 未加载。"
                "请在 .env 中填入真实阿里云凭证，或在界面将线路切换至【模拟外呼通道 (Mock)】。"
            )
            logger.warning(msg)
            return CallResult(
                success=False,
                call_id="",
                message=msg,
                provider="aliyun",
                raw_response={"error": "MISSING_CREDENTIALS"}
            )

        try:
            req = dyvms_models.SingleCallByTtsRequest(
                called_number=phone,
                tts_code=target_template,
                tts_param=tts_param_str,
                play_times=2,  # 播报 2 遍
                volume=100
            )
            if self.called_show_number:
                req.called_show_number = self.called_show_number

            runtime = util_models.RuntimeOptions()
            logger.info(f"【阿里云语音外呼】准备向真实手机号 [{phone}] 发起外呼，模板: [{target_template}]，参数: {tts_param_str}")

            # 调用阿里云官方 API
            response = self.client.single_call_by_tts_with_options(req, runtime)
            resp_body = response.body

            if resp_body.code == "OK":
                call_id = resp_body.call_id or ""
                logger.info(f"【阿里云语音外呼成功】手机号: {phone}, CallId: {call_id}")
                return CallResult(
                    success=True,
                    call_id=call_id,
                    message="阿里云外呼指令下发成功，正在拨打振铃中",
                    provider="aliyun",
                    raw_response={"Code": resp_body.code, "CallId": call_id, "RequestId": resp_body.request_id}
                )
            else:
                err_msg = f"阿里云返回业务异常: [{resp_body.code}] {resp_body.message}"
                logger.error(f"【阿里云语音外呼失败】{err_msg}")
                return CallResult(
                    success=False,
                    call_id="",
                    message=err_msg,
                    provider="aliyun",
                    raw_response={"Code": resp_body.code, "Message": resp_body.message, "RequestId": resp_body.request_id}
                )

        except Exception as e:
            err_msg = f"调用阿里云语音服务底层网络/API异常: {str(e)}"
            logger.exception(err_msg)
            return CallResult(
                success=False,
                call_id="",
                message=err_msg,
                provider="aliyun",
                raw_response={"exception": str(e)}
            )

    async def query_call_status(self, call_id: str) -> Dict[str, Any]:
        """查询呼叫详情"""
        if not self.client or not call_id:
            return {"status": "UNKNOWN", "call_id": call_id}
        try:
            # dyvmsapi query call detail
            req = dyvms_models.QueryCallDetailByCallIdRequest(call_id=call_id, prod_id=11000000300004)
            resp = self.client.query_call_detail_by_call_id(req)
            return {"Code": resp.body.code, "Data": resp.body.data}
        except Exception as e:
            logger.warning(f"查询阿里云呼叫状态失败: {e}")
            return {"status": "ERROR", "message": str(e)}
