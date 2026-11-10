from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.session import Base

if TYPE_CHECKING:
    from app.models.alarm import Alarm


class WorkOrder(Base):
    __tablename__ = "work_orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_code: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    alarm_id: Mapped[int] = mapped_column(ForeignKey("alarms.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    priority: Mapped[str] = mapped_column(String(16), default="P1", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False, index=True)
    # PENDING(待接单), IN_PROGRESS(排查维修中), COMPLETED(维修完成), CANCELLED(已作废), CLOSED(已闭环关闭)

    assignee: Mapped[str] = mapped_column(String(64), default="", nullable=False)  # 指派责任人 (如李主管)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    ai_suggestion: Mapped[str] = mapped_column(Text, default="", nullable=False)
    steps: Mapped[Optional[list]] = mapped_column(JSON, default=list)  # 排查处置打勾项
    solution_note: Mapped[str] = mapped_column(Text, default="", nullable=False)  # 现场处理结果说明

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    alarm: Mapped["Alarm"] = relationship(back_populates="work_orders")
