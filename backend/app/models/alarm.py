from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import String, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.session import Base

if TYPE_CHECKING:
    from app.models.device import Device
    from app.models.alarm_event import AlarmEvent
    from app.models.ai_analysis import AIAnalysis
    from app.models.call import CallRecord
    from app.models.workorder import WorkOrder


class Alarm(Base):
    __tablename__ = "alarms"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    level: Mapped[str] = mapped_column(String(16), default="P1", nullable=False)  # P1, P2, P3
    status: Mapped[str] = mapped_column(String(32), default="TRIGGERED", nullable=False, index=True)
    # 状态枚举：TRIGGERED, ACKNOWLEDGED, PROCESSING, RESOLVED, CLOSED

    metric_name: Mapped[str] = mapped_column(String(64), nullable=False)  # 如: pressure, temperature, current
    trigger_value: Mapped[float] = mapped_column(Float, nullable=False)  # 触发时的异常测量值
    threshold: Mapped[float] = mapped_column(Float, nullable=False)  # 设定的报警阈值
    unit: Mapped[str] = mapped_column(String(32), default="", nullable=False)  # MPa, ℃, A
    message: Mapped[str] = mapped_column(Text, nullable=False)  # 报警详细说明

    ai_analysis_status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False)
    # PENDING, ANALYZING, COMPLETED, FAILED

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    device: Mapped["Device"] = relationship(back_populates="alarms")
    events: Mapped[List["AlarmEvent"]] = relationship(back_populates="alarm", cascade="all, delete-orphan", order_by="AlarmEvent.created_at.desc()")
    ai_analysis: Mapped[Optional["AIAnalysis"]] = relationship(back_populates="alarm", uselist=False, cascade="all, delete-orphan")
    call_records: Mapped[List["CallRecord"]] = relationship(back_populates="alarm", cascade="all, delete-orphan", order_by="CallRecord.created_at.desc()")
    work_orders: Mapped[List["WorkOrder"]] = relationship(back_populates="alarm", cascade="all, delete-orphan")
