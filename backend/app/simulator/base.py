from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, List
from pydantic import BaseModel, Field


class DeviceData(BaseModel):
    """
    标准化的设备遥测数据包 (DeviceData)
    报警规则引擎与上层平台仅依赖此标准化结构，实现与物理数据源（模拟器/OPC-UA/Modbus/MQTT）解耦
    """
    device_code: str = Field(..., description="设备唯一编码，如 PUMP-001")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="采集时间戳")
    metrics: Dict[str, float] = Field(default_factory=dict, description="遥测指标字典，如 {'pressure': 24.8, 'temp': 58.2}")
    status: str = Field(default="RUNNING", description="运行工况：RUNNING, ALARMING, OFFLINE, MAINTENANCE")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="扩展元数据")


class BaseDeviceProvider(ABC):
    """设备接入层抽象适配器基类"""

    @abstractmethod
    async def fetch_latest_data(self) -> List[DeviceData]:
        """获取所有接入设备的最新数据包"""
        pass

    @abstractmethod
    def set_scenario(self, device_code: str, scenario_name: str, **kwargs):
        """为特定设备设置运行场景（正常/故障注入）"""
        pass
