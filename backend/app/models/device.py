from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.session import Base

if TYPE_CHECKING:
    from app.models.alarm import Alarm


class Device(Base):
    __tablename__ = "devices"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    type: Mapped[str] = mapped_column(String(64), nullable=False)  # 如: HYDRAULIC_PUMP, MOTOR, CNC
    location: Mapped[str] = mapped_column(String(128), nullable=False)  # 车间/工位
    status: Mapped[str] = mapped_column(String(32), default="RUNNING", nullable=False)  # RUNNING, ALARMING, OFFLINE, MAINTENANCE
    metrics: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)  # 最新遥测快照 (压力、温度、电流等)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    alarms: Mapped[List["Alarm"]] = relationship(back_populates="device", cascade="all, delete-orphan")
