from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.session import Base

if TYPE_CHECKING:
    from app.models.alarm import Alarm


class CallRecord(Base):
    __tablename__ = "call_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    alarm_id: Mapped[int] = mapped_column(ForeignKey("alarms.id", ondelete="CASCADE"), nullable=False, index=True)
    contact_name: Mapped[str] = mapped_column(String(64), nullable=False)
    contact_phone: Mapped[str] = mapped_column(String(32), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=1, nullable=False)  # 第几次拨打轮次 / 联系人优先级
    provider: Mapped[str] = mapped_column(String(32), default="aliyun", nullable=False)  # aliyun, mock
    call_id: Mapped[str] = mapped_column(String(128), default="", index=True, nullable=False)  # 阿里云返回的呼叫任务ID或本地唯一号
    status: Mapped[str] = mapped_column(String(32), default="CALLING", nullable=False, index=True)
    # CALLING, ANSWERED, UNANSWERED, TIMEOUT, FAILED, ESCALATED
    duration: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # 通话时长(秒)
    template_code: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    template_params: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    callback_payload: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)  # 回执原始报文
    error_msg: Mapped[str] = mapped_column(Text, default="", nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    answered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    alarm: Mapped["Alarm"] = relationship(back_populates="call_records")
