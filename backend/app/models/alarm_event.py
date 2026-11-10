from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.session import Base

if TYPE_CHECKING:
    from app.models.alarm import Alarm


class AlarmEvent(Base):
    __tablename__ = "alarm_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    alarm_id: Mapped[int] = mapped_column(ForeignKey("alarms.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)  # TRIGGER, CALL_INIT, CALL_TIMEOUT, CALL_ANSWERED, ACKNOWLEDGE, WORKORDER_CREATED, RESOLVED, CLOSED
    from_status: Mapped[str] = mapped_column(String(32), nullable=False)
    to_status: Mapped[str] = mapped_column(String(32), nullable=False)
    operator: Mapped[str] = mapped_column(String(64), default="SYSTEM", nullable=False)
    note: Mapped[str] = mapped_column(Text, default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    alarm: Mapped["Alarm"] = relationship(back_populates="events")
