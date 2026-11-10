import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from app.simulator.base import DeviceData
from app.services.alarm.service import alarm_service

logger = logging.getLogger(__name__)


class AlarmRuleEngine:
    """
    工业告警判定规则引擎
    严格遵循适配器模式：仅接收标准化 DeviceData 结构，无需关心数据来源于模拟器、OPC-UA、Modbus 或 MQTT
    """

    def __init__(self):
        # 预设工业设备报警阈值矩阵
        self.rules = [
            {
                "metric": "pressure",
                "condition": "lt",
                "threshold": 18.0,
                "unit": "MPa",
                "level": "P1",
                "title_template": "{device_name} 主泵出口压力异常骤降失压",
                "message_template": "主泵出口压力当前为 {val} MPa，已跌破安全下限阈值 18.0 MPa，可能存在液压系统高压内泄或爆管风险！"
            },
            {
                "metric": "current",
                "condition": "gt",
                "threshold": 75.0,
                "unit": "A",
                "level": "P2",
                "title_template": "{device_name} 定子工作电流突发严重过载",
                "message_template": "电机运行电流当前为 {val} A，超出额定过载阈值 75.0 A，持续过载将导致电机绕组绝缘击穿！"
            },
            {
                "metric": "temperature",
                "condition": "gt",
                "threshold": 90.0,
                "unit": "℃",
                "level": "P2",
                "title_template": "{device_name} 关键传动轴承温度急剧超温",
                "message_template": "轴承工作温度监测值为 {val} ℃，超出允许警戒温升 90.0 ℃，轴承面临烧蚀抱死风险！"
            }
        ]

    async def evaluate_device_data(self, session: Session, data: DeviceData):
        """
        评估单台设备的遥测数据包
        """
        device_code = data.device_code
        device_name = data.metadata.get("name", device_code)

        # 1. 评估离线告警
        if data.status == "OFFLINE":
            await alarm_service.trigger_alarm(
                session=session,
                device_code=device_code,
                title=f"{device_name} 遥测通讯链路中断离线",
                level="P3",
                metric_name="status",
                trigger_value=0.0,
                threshold=1.0,
                unit="heartbeat",
                message=f"设备心跳丢失超过 15 秒，网络连接超时重置，已切换为离线状态。"
            )
            return

        # 2. 评估常规遥测指标越限
        metrics = data.metrics
        for rule in self.rules:
            metric_key = rule["metric"]
            if metric_key not in metrics:
                continue

            val = float(metrics[metric_key])
            is_triggered = False

            if rule["condition"] == "lt" and val < rule["threshold"]:
                is_triggered = True
            elif rule["condition"] == "gt" and val > rule["threshold"]:
                is_triggered = True

            if is_triggered:
                title = rule["title_template"].format(device_name=device_name)
                msg = rule["message_template"].format(val=val)
                await alarm_service.trigger_alarm(
                    session=session,
                    device_code=device_code,
                    title=title,
                    level=rule["level"],
                    metric_name=metric_key,
                    trigger_value=val,
                    threshold=rule["threshold"],
                    unit=rule["unit"],
                    message=msg
                )


alarm_rule_engine = AlarmRuleEngine()
