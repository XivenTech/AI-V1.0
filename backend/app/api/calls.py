from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.call import CallRecord
from app.models.alarm import Alarm
from app.schemas.call import CallTriggerRequest, CallRecordResponse, AliyunCallbackPayload, CallSimulateRequest
from app.services.call.service import call_service
from app.core.config import settings

router = APIRouter(prefix="/api/calls", tags=["语音呼叫中心"])


@router.get("/config", summary="获取当前外呼通道与配置状态")
def get_call_config():
    return {
        "current_provider": call_service.current_provider_name,
        "has_aliyun_credentials": bool(settings.ALIBABA_CLOUD_ACCESS_KEY_ID and settings.ALIBABA_CLOUD_ACCESS_KEY_SECRET),
        "tts_code": settings.TTS_CODE,
        "timeout_seconds": settings.CALL_TIMEOUT_SECONDS
    }


@router.post("/config/provider", summary="切换当前默认呼叫通道 (aliyun / mock)")
def switch_call_provider(provider: str = Query(..., regex="^(aliyun|mock)$")):
    call_service.set_active_provider(provider)
    return {"message": f"呼叫通道已成功切换为: {provider}", "current_provider": provider}


@router.get("/records", response_model=List[CallRecordResponse], summary="查询外呼通话记录列表")
def get_call_records(
    alarm_id: Optional[int] = Query(None, description="报警ID过滤"),
    db: Session = Depends(get_db)
):
    stmt = select(CallRecord).order_by(CallRecord.created_at.desc())
    if alarm_id:
        stmt = stmt.where(CallRecord.alarm_id == alarm_id)
    records = db.execute(stmt).scalars().all()
    return records


@router.post("/trigger", response_model=CallRecordResponse, summary="手动/测试触发单次语音外呼 (支持真实手机号)")
async def trigger_call(
    req: CallTriggerRequest,
    db: Session = Depends(get_db)
):
    """
    手动发起外呼：
    - 若指定了 alarm_id，关联该报警并使用报警详情
    - 若未指定 alarm_id，使用虚拟测试报警或默认参数直接拨打真实手机号
    """
    alarm_id = req.alarm_id
    if not alarm_id:
        # 获取最新的一个报警作为上下文，或新建一个演练报警
        stmt = select(Alarm).order_by(Alarm.created_at.desc())
        latest_alarm = db.execute(stmt).scalars().first()
        if latest_alarm:
            alarm_id = latest_alarm.id
        else:
            raise HTTPException(status_code=400, detail="系统中暂无报警记录，请先在演示模式中触发场景或指定有效的 alarm_id")

    provider = req.provider or call_service.current_provider_name

    # 发起呼叫
    call_record = await call_service.initiate_alarm_call(
        session=db,
        alarm_id=alarm_id,
        priority=1,
        provider_name=provider
    )
    return call_record


@router.post("/callback/aliyun", summary="阿里云语音服务 Webhook 回执接收端点")
async def aliyun_call_callback(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    接收阿里云语音服务 (Dyvmsapi) 呼叫状态异步回执：
    包含 call_id, status_code, duration 等，自动更新 CallRecord 并流转通知/报警/工单状态机
    """
    try:
        body = await request.json()
    except Exception:
        # 兼容 form-data 或 query 参数
        form_data = await request.form()
        body = dict(form_data) if form_data else dict(request.query_params)

    await call_service.handle_aliyun_callback(db, body)
    return {"code": 0, "msg": "SUCCESS"}


@router.post("/simulate-action", summary="演示模式：快捷模拟接听/超时拒接动作")
async def simulate_call_action(
    req: CallSimulateRequest,
    db: Session = Depends(get_db)
):
    """
    供前端现场演示快速把控节奏使用：
    - action='ANSWER': 模拟值班人员接听电话
    - action='TIMEOUT': 模拟超时未接听，自动触发升级拨打李主管
    - action='REJECT': 模拟拒接
    """
    record_id = req.call_record_id
    if not record_id:
        # 查找最新一条处于 CALLING 状态的呼叫
        stmt = select(CallRecord).where(CallRecord.status == "CALLING").order_by(CallRecord.created_at.desc())
        rec = db.execute(stmt).scalars().first()
        if not rec:
            raise HTTPException(status_code=400, detail="当前没有正在呼叫中的电话记录")
        record_id = rec.id

    if req.action == "ANSWER":
        updated_rec = await call_service.handle_call_answered(db, record_id, duration=25)
        return {"message": "已成功模拟接听，已同步确认报警并生成维修工单", "call_record_id": updated_rec.id}
    elif req.action in ("TIMEOUT", "REJECT"):
        is_to = (req.action == "TIMEOUT")
        res = await call_service.handle_call_timeout_or_reject(db, record_id, is_timeout=is_to)
        return {
            "message": "已成功模拟超时未接听/拒接，状态机已触发自动升级流程",
            "escalated_call_id": res.id if res else None
        }
    else:
        raise HTTPException(status_code=400, detail="不支持的模拟动作，允许值: ANSWER, TIMEOUT, REJECT")
