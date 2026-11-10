import asyncio
import logging
from datetime import datetime
from sqlalchemy import select
from app.database.session import SessionLocal
from app.models.device import Device
from app.simulator.provider import simulator_provider
from app.alarm_engine.engine import alarm_rule_engine
from app.websocket.manager import websocket_manager

logger = logging.getLogger(__name__)


class DataGeneratorTask:
    """设备遥测数据流水线异步驱动任务"""

    def __init__(self):
        self._running = False
        self._task: asyncio.Task = None

    def start(self):
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._run_loop())
            logger.info("【数据流引擎】设备仿真流水线后台协程已启动")

    def stop(self):
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            logger.info("【数据流引擎】设备仿真流水线后台协程已暂停")

    async def _run_loop(self):
        while self._running:
            try:
                # 1. 从 DeviceProvider 采集标准化 DeviceData
                data_list = await simulator_provider.fetch_latest_data()

                db = SessionLocal()
                try:
                    for data in data_list:
                        # 2. 持久化同步设备最新遥测与工况
                        stmt = select(Device).where(Device.code == data.device_code)
                        device = db.execute(stmt).scalars().first()
                        if device:
                            device.metrics = data.metrics
                            if data.status == "OFFLINE":
                                device.status = "OFFLINE"
                            elif device.status != "ALARMING":
                                device.status = data.status
                            device.updated_at = datetime.utcnow()
                            db.commit()

                        # 3. 送入报警规则引擎评估
                        await alarm_rule_engine.evaluate_device_data(db, data)

                    # 4. 广播实时遥测至前端大屏驱动 ECharts 动态走线
                    await websocket_manager.broadcast(
                        "telemetry_update",
                        {
                            "timestamp": datetime.now().strftime("%H:%M:%S"),
                            "devices": [
                                {
                                    "code": d.device_code,
                                    "status": d.status,
                                    "metrics": d.metrics
                                }
                                for d in data_list
                            ]
                        }
                    )
                finally:
                    db.close()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"数据生成与评估协程循环异常: {e}")

            # 仿真采集周期 1.5 秒
            await asyncio.sleep(1.5)


data_generator_task = DataGeneratorTask()
