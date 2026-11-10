from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Float, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.session import Base

if TYPE_CHECKING:
    from app.models.alarm import Alarm


class AIAnalysis(Base):
    __tablename__ = "ai_analyses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    alarm_id: Mapped[int] = mapped_column(ForeignKey("alarms.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    root_cause: Mapped[str] = mapped_column(String(256), nullable=False)  # 判定根因
    confidence: Mapped[float] = mapped_column(Float, default=0.95, nullable=False)  # 置信度 (0.0~1.0)
    risk_level: Mapped[str] = mapped_column(String(32), default="HIGH", nullable=False)  # CRITICAL, HIGH, MEDIUM, LOW
    suggestion: Mapped[str] = mapped_column(Text, nullable=False)  # 应急处置方案建议
    checklist: Mapped[Optional[list]] = mapped_column(JSON, default=list)  # 现场排查步骤清单
    raw_response: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    alarm: Mapped["Alarm"] = relationship(back_populates="ai_analysis")
