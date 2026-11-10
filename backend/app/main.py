import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.core.config import settings
from app.database.session import engine, Base, SessionLocal
from app.models import Device, Contact, Alarm, CallRecord, AlarmEvent, AIAnalysis, WorkOrder
from app.api import api_router
from app.websocket.manager import websocket_manager
from app.simulator.generator import data_generator_task

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("main")


def init_seed_data():
    """初始化预置演示数据（设备及应急值班联系人）"""
    db = SessionLocal()
    try:
        # 1. 初始化预设核心设备
        existing_device = db.execute(select(Device)).scalars().first()
        if not existing_device:
            devices = [
                Device(
                    code="PUMP-001",
                    name="#1 主液压动力总成",
                    type="HYDRAULIC_PUMP",
                    location="A区-主液压泵房",
                    status="RUNNING",
                    metrics={"pressure": 25.0, "temperature": 58.0, "current": 42.5, "vibration": 1.8, "flow": 120.0}
                ),
                Device(
                    code="MOTOR-002",
                    name="#2 粗轧高速重载电机",
                    type="MOTOR",
                    location="B区-粗轧机列",
                    status="RUNNING",
                    metrics={"pressure": 0.0, "temperature": 60.5, "current": 44.0, "vibration": 2.1, "flow": 0.0}
                ),
                Device(
                    code="CNC-003",
                    name="#3 五轴精密加工中心",
                    type="CNC",
                    location="C区-恒温精密车间",
                    status="RUNNING",
                    metrics={"pressure": 6.2, "temperature": 32.0, "current": 18.5, "vibration": 0.8, "flow": 45.0}
                )
            ]
            db.add_all(devices)
            db.commit()
            logger.info("【数据库初始化】预置 3 台核心工业设备创建完成")

        # 2. 初始化应急值班联系人 (第1联系人张工，第2联系人李主管)
        existing_contact = db.execute(select(Contact)).scalars().first()
        if not existing_contact:
            contacts = [
                Contact(
                    name=settings.DEMO_PRIMARY_CONTACT_NAME,
                    role="一线值班工程师",
                    phone=settings.DEMO_PRIMARY_CONTACT_PHONE,
                    priority=1,
                    is_active=True
                ),
                Contact(
                    name=settings.DEMO_SECONDARY_CONTACT_NAME,
                    role="车间值班主管",
                    phone=settings.DEMO_SECONDARY_CONTACT_PHONE,
                    priority=2,
                    is_active=True
                )
            ]
            db.add_all(contacts)
            db.commit()
            logger.info(f"【数据库初始化】预置 2 名值班联系人: {contacts[0].name} ({contacts[0].phone}), {contacts[1].name} ({contacts[1].phone})")

    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动前初始化数据表
    Base.metadata.create_all(bind=engine)
    init_seed_data()

    # 启动后台设备数据流引擎
    data_generator_task.start()
    logger.info("【系统启动】AI无人值守工厂智能告警与自动处置平台初始化就绪")

    yield

    # 关闭后台任务
    data_generator_task.stop()
    logger.info("【系统关闭】后台服务已优雅退出")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载 API
app.include_router(api_router)


@app.get("/health", summary="系统健康检查")
def health_check():
    return {
        "status": "UP",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "call_provider": settings.CALL_PROVIDER
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """前端大屏 WebSocket 实时通信通道"""
    await websocket_manager.connect(websocket)
    try:
        while True:
            # 保持心跳侦听
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket 异常断开: {e}")
        websocket_manager.disconnect(websocket)
