import asyncio
import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import select, delete
from sqlalchemy.orm import Session
from app.database.session import get_db, SessionLocal
from app.models.device import Device
from app.models.alarm import Alarm
from app.models.alarm_event import AlarmEvent
from app.models.call import CallRecord
from app.models.ai_analysis import AIAnalysis
from app.models.workorder import WorkOrder
from app.simulator.provider import simulator_provider
from app.schemas.demo import ScenarioTriggerRequest
from app.websocket.manager import websocket_manager
from app.services.call.service import call_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/demo", tags=["演示模式控制台"])


@router.post("/trigger-scenario", summary="一键切换演示工况场景")
async def trigger_scenario(
    req: ScenarioTriggerRequest,
    db: Session = Depends(get_db)
):
    """
    触发演示场景：
    - HYDRAULIC_LEAK: 模拟主泵内泄失压 (P1 级严重告警)
    - MOTOR_OVERHEAT: 模拟电机重载过流与轴承超温 (P2 级告警)
    - DEVICE_OFFLINE: 模拟设备丢包断网离线 (P3 级告警)
    - RESET: 一键复位恢复初始健康工况
    """
    scenario = req.scenario.upper()

    if scenario == "RESET":
        simulator_provider.reset_all()

        # 复位数据库中设备状态
        devices = db.execute(select(Device)).scalars().all()
        for dev in devices:
            dev.status = "RUNNING"
            if dev.code == "PUMP-001":
                dev.metrics = {"pressure": 25.0, "temperature": 58.0, "current": 42.5, "vibration": 1.8, "flow": 120.0}
            elif dev.code == "MOTOR-002":
                dev.metrics = {"pressure": 0.0, "temperature": 60.5, "current": 44.0, "vibration": 2.1, "flow": 0.0}
            elif dev.code == "CNC-003":
                dev.metrics = {"pressure": 6.2, "temperature": 32.0, "current": 18.5, "vibration": 0.8, "flow": 45.0}

        db.commit()

        # 广播复位消息
        await websocket_manager.broadcast("demo_reset", {"message": "系统仿真工况已全量复位为初始健康状态"})
        return {"status": "SUCCESS", "scenario": "RESET", "message": "全系统已复位"}

    # 故障注入设备映射
    target_code = req.device_code
    if not target_code:
        if scenario == "HYDRAULIC_LEAK":
            target_code = "PUMP-001"
        elif scenario == "MOTOR_OVERHEAT":
            target_code = "MOTOR-002"
        elif scenario == "DEVICE_OFFLINE":
            target_code = "CNC-003"
        else:
            target_code = "PUMP-001"

    simulator_provider.set_scenario(target_code, scenario)

    await websocket_manager.broadcast(
        "scenario_injected",
        {
            "scenario": scenario,
            "device_code": target_code,
            "message": f"已成功向设备 [{target_code}] 注入场景: {scenario}"
        }
    )

    return {
        "status": "SUCCESS",
        "scenario": scenario,
        "device_code": target_code,
        "message": f"故障场景 [{scenario}] 注入成功，仿真引擎将在下一周期触发指标异动与报警规则"
    }


@router.post("/golden-path/start", summary="启动 3 分钟黄金路径全流程自动演示演练")
async def start_golden_path(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    3 分钟现场黄金闭环演示编排器：
    依次自动化推进：
    1. 注入主泵失压数据 -> 产生 P1 告警
    2. 发起第一联系人真实呼叫 + 启动 AI 根因推导
    3. 8秒后第一联系人超时未接听 -> 自动触发状态机升级，呼叫第二联系人（李主管）
    4. 6秒后第二联系人接听电话 -> 自动生成维修工单
    5. 自动指派与流转工单 -> 演示最终闭环恢复
    """
    background_tasks.add_task(_execute_golden_path_orchestration)
    return {
        "status": "STARTED",
        "message": "3分钟黄金演示全流程已启动，请在大屏关注呼叫监控卡片与状态机联动流转！"
    }


async def _execute_golden_path_orchestration():
    """黄金路径自动化协程"""
    logger.info("【黄金演示编排】启动 3 分钟黄金路径闭环演练...")
    await websocket_manager.broadcast(
        "golden_path_step",
        {"step": 1, "title": "设备压力异动", "message": "正在模拟液压系统内部微裂纹发展，主泵出口压力由 25.0 MPa 持续走低..."}
    )

    # 1. 注入液压泄漏故障
    simulator_provider.set_scenario("PUMP-001", "HYDRAULIC_LEAK")
    await asyncio.sleep(3.5)

    # 2. 等待告警产生并捕获呼叫记录
    db = SessionLocal()
    try:
        stmt = select(Alarm).where(Alarm.device_id == 1, Alarm.status == "TRIGGERED").order_by(Alarm.created_at.desc())
        alarm = db.execute(stmt).scalars().first()

        if alarm:
            await websocket_manager.broadcast(
                "golden_path_step",
                {"step": 2, "title": "P1严重告警触发", "message": f"触发 P1 级严重液压报警 #{alarm.id}，AI 异步推导与电话外呼并发启动！"}
            )
            await asyncio.sleep(6.0)

            # 3. 模拟第一联系人超时未接听 -> 触发升级
            call_stmt = select(CallRecord).where(CallRecord.alarm_id == alarm.id, CallRecord.priority == 1, CallRecord.status == "CALLING")
            first_call = db.execute(call_stmt).scalars().first()
            if first_call:
                await websocket_manager.broadcast(
                    "golden_path_step",
                    {"step": 3, "title": "第一联系人超时升级", "message": f"第一联系人 [{first_call.contact_name}] 未接听，状态机判定超时并启动升级外呼！"}
                )
                await call_service.handle_call_timeout_or_reject(db, first_call.id, is_timeout=True)
                await asyncio.sleep(5.0)

            # 4. 第二联系人接听电话
            sec_call_stmt = select(CallRecord).where(CallRecord.alarm_id == alarm.id, CallRecord.priority == 2, CallRecord.status == "CALLING")
            sec_call = db.execute(sec_call_stmt).scalars().first()
            if sec_call:
                await websocket_manager.broadcast(
                    "golden_path_step",
                    {"step": 4, "title": "第二联系人接听确认", "message": f"第二联系人 [{sec_call.contact_name}] 成功接听电话并听取 TTS 语音告警，自动派发维修工单！"}
                )
                await call_service.handle_call_answered(db, sec_call.id, duration=32)
                await asyncio.sleep(4.0)

            # 5. 查看工单并模拟现场检修完成
            wo_stmt = select(WorkOrder).where(WorkOrder.alarm_id == alarm.id)
            wo = db.execute(wo_stmt).scalars().first()
            if wo:
                await websocket_manager.broadcast(
                    "golden_path_step",
                    {"step": 5, "title": "现场排查维修完成", "message": f"工单 #{wo.order_code} 现场维修完成，双状态机联动闭环恢复！"}
                )
                from app.state_machine.workorder import WorkOrderStateMachine
                WorkOrderStateMachine.transition(
                    session=db,
                    workorder=wo,
                    target_state="COMPLETED",
                    operator="李主管",
                    solution_note="更换主泵单向阀阀芯密封环并锁定旁路，液压压力恢复至 25.0 MPa 额定压力。"
                )
                # 恢复设备工况
                simulator_provider.reset_all()

    finally:
        db.close()
