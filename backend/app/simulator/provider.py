import logging
from datetime import datetime
from typing import Dict, List, Any
from app.simulator.base import BaseDeviceProvider, DeviceData
from app.simulator.scenarios import ScenarioModel

logger = logging.getLogger(__name__)


class SimulatorProvider(BaseDeviceProvider):
    """
    工业设备数据仿真适配器 Provider
    满足适配器模式规范：未来更换为 OpcUaProvider / ModbusProvider 时，无需变动任何规则引擎与状态机代码
    """

    def __init__(self):
        # 初始仿真设备清单
        self.devices_state: Dict[str, Dict[str, Any]] = {
            "PUMP-001": {
                "name": "#1 主液压动力总成",
                "type": "HYDRAULIC_PUMP",
                "location": "A区-主液压泵房",
                "status": "RUNNING",
                "scenario": "NORMAL",
                "step_count": 0,
                "metrics": {
                    "pressure": 25.0,
                    "temperature": 58.0,
                    "current": 42.5,
                    "vibration": 1.8,
                    "flow": 120.0
                }
            },
            "MOTOR-002": {
                "name": "#2 粗轧高速重载电机",
                "type": "MOTOR",
                "location": "B区-粗轧机列",
                "status": "RUNNING",
                "scenario": "NORMAL",
                "step_count": 0,
                "metrics": {
                    "pressure": 0.0,
                    "temperature": 60.5,
                    "current": 44.0,
                    "vibration": 2.1,
                    "flow": 0.0
                }
            },
            "CNC-003": {
                "name": "#3 五轴精密加工中心",
                "type": "CNC",
                "location": "C区-恒温精密车间",
                "status": "RUNNING",
                "scenario": "NORMAL",
                "step_count": 0,
                "metrics": {
                    "pressure": 6.2,
                    "temperature": 32.0,
                    "current": 18.5,
                    "vibration": 0.8,
                    "flow": 45.0
                }
            }
        }

    def set_scenario(self, device_code: str, scenario_name: str, **kwargs):
        """设定指定设备的工况场景"""
        if device_code in self.devices_state:
            dev = self.devices_state[device_code]
            dev["scenario"] = scenario_name
            dev["step_count"] = 0
            if scenario_name == "DEVICE_OFFLINE":
                dev["status"] = "OFFLINE"
            elif scenario_name in ("HYDRAULIC_LEAK", "MOTOR_OVERHEAT"):
                dev["status"] = "ALARMING"
            else:
                dev["status"] = "RUNNING"
            logger.info(f"【设备模拟器】设备 {device_code} 切换至工况场景: {scenario_name}")
        else:
            logger.warning(f"设备不存在: {device_code}")

    def reset_all(self):
        """重置所有设备为初始正常工况"""
        for code, dev in self.devices_state.items():
            dev["scenario"] = "NORMAL"
            dev["status"] = "RUNNING"
            dev["step_count"] = 0
            if code == "PUMP-001":
                dev["metrics"] = {"pressure": 25.0, "temperature": 58.0, "current": 42.5, "vibration": 1.8, "flow": 120.0}
            elif code == "MOTOR-002":
                dev["metrics"] = {"pressure": 0.0, "temperature": 60.5, "current": 44.0, "vibration": 2.1, "flow": 0.0}
            elif code == "CNC-003":
                dev["metrics"] = {"pressure": 6.2, "temperature": 32.0, "current": 18.5, "vibration": 0.8, "flow": 45.0}
        logger.info("【设备模拟器】所有设备均已复位至初始正常工况")

    async def fetch_latest_data(self) -> List[DeviceData]:
        """按步长推进物理仿真，并返回标准 DeviceData 集合"""
        result: List[DeviceData] = []
        now = datetime.utcnow()

        for code, state in self.devices_state.items():
            scenario = state["scenario"]
            step_count = state["step_count"]
            current_metrics = state["metrics"]

            if scenario == "DEVICE_OFFLINE":
                # 离线设备不产生有效指标或产生离线状态数据
                result.append(
                    DeviceData(
                        device_code=code,
                        timestamp=now,
                        metrics=current_metrics,
                        status="OFFLINE",
                        metadata={"error": "Heartbeat packet loss, TCP connection reset"}
                    )
                )
                continue

            if scenario == "HYDRAULIC_LEAK":
                next_metrics = ScenarioModel.hydraulic_leak_step(current_metrics, step_count)
            elif scenario == "MOTOR_OVERHEAT":
                next_metrics = ScenarioModel.motor_overheat_step(current_metrics, step_count)
            else:
                next_metrics = ScenarioModel.normal_step(current_metrics)

            state["step_count"] += 1
            state["metrics"] = next_metrics

            result.append(
                DeviceData(
                    device_code=code,
                    timestamp=now,
                    metrics=next_metrics,
                    status=state["status"],
                    metadata={"scenario": scenario, "name": state["name"]}
                )
            )

        return result


simulator_provider = SimulatorProvider()
