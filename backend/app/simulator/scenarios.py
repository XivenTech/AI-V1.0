import random
from typing import Dict, Any


class ScenarioModel:
    """定义仿真物理量动态演化计算逻辑"""

    @staticmethod
    def normal_step(current_metrics: Dict[str, float]) -> Dict[str, float]:
        """正常工况：参数在额定区间平稳小幅高斯白噪声波动"""
        pressure = current_metrics.get("pressure", 25.0)
        # 目标基准 25.0 MPa，受控平稳波动
        pressure += random.uniform(-0.15, 0.15)
        pressure = max(24.2, min(25.8, pressure))

        temperature = current_metrics.get("temperature", 58.0)
        temperature += random.uniform(-0.2, 0.2)
        temperature = max(55.0, min(62.0, temperature))

        current = current_metrics.get("current", 42.5)
        current += random.uniform(-0.5, 0.5)
        current = max(40.0, min(45.5, current))

        vibration = current_metrics.get("vibration", 1.8)
        vibration += random.uniform(-0.05, 0.05)
        vibration = max(1.5, min(2.2, vibration))

        flow = current_metrics.get("flow", 120.0)
        flow += random.uniform(-1.0, 1.0)
        flow = max(115.0, min(125.0, flow))

        return {
            "pressure": round(pressure, 2),
            "temperature": round(temperature, 1),
            "current": round(current, 1),
            "vibration": round(vibration, 2),
            "flow": round(flow, 1),
        }

    @staticmethod
    def hydraulic_leak_step(current_metrics: Dict[str, float], step_count: int) -> Dict[str, float]:
        """
        场景 1：主液压泵内泄/失压故障 (P1 级严重告警)
        物理特征：主泵出口压力由 25.0 MPa 骤降并持续探底至 12.0 MPa (阈值 18.0 MPa)；
        伴随脉动振动加剧与输出流量跌落
        """
        pressure = current_metrics.get("pressure", 25.0)
        # 随步数快速下滑
        drop_rate = 1.2 + (step_count * 0.15)
        pressure = max(11.2, pressure - drop_rate + random.uniform(-0.2, 0.1))

        flow = current_metrics.get("flow", 120.0)
        flow = max(68.0, flow - 3.5 + random.uniform(-1.0, 1.0))

        vibration = current_metrics.get("vibration", 1.8)
        vibration = min(5.8, vibration + 0.35 + random.uniform(0.0, 0.15))

        temperature = current_metrics.get("temperature", 58.0)
        temperature = min(78.0, temperature + 0.4)

        current = current_metrics.get("current", 42.5)

        return {
            "pressure": round(pressure, 2),
            "temperature": round(temperature, 1),
            "current": round(current, 1),
            "vibration": round(vibration, 2),
            "flow": round(flow, 1),
        }

    @staticmethod
    def motor_overheat_step(current_metrics: Dict[str, float], step_count: int) -> Dict[str, float]:
        """
        场景 2：电机重载过流与轴承超温故障 (P2 级告警)
        物理特征：电流激增突破额定值 (45A -> 88A+，阈值 70A)，定子/轴承温度持续攀升破百 (58℃ -> 105℃)
        """
        current = current_metrics.get("current", 42.5)
        current = min(96.0, current + 4.5 + random.uniform(-0.5, 0.8))

        temperature = current_metrics.get("temperature", 58.0)
        temperature = min(108.0, temperature + 2.8 + random.uniform(0.0, 0.5))

        vibration = current_metrics.get("vibration", 1.8)
        vibration = min(4.6, vibration + 0.2)

        pressure = current_metrics.get("pressure", 25.0)
        flow = current_metrics.get("flow", 120.0)

        return {
            "pressure": round(pressure, 2),
            "temperature": round(temperature, 1),
            "current": round(current, 1),
            "vibration": round(vibration, 2),
            "flow": round(flow, 1),
        }
