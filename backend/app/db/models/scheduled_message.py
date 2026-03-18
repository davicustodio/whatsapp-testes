from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDTimestampMixin


class ScheduledMessage(Base, UUIDTimestampMixin):
    __tablename__ = "scheduled_messages"

    instance_id: Mapped[str] = mapped_column(ForeignKey("instances.id", ondelete="CASCADE"), index=True)
    recipients: Mapped[list[dict]] = mapped_column(JSON)
    content: Mapped[str] = mapped_column(Text)
    message_type: Mapped[str] = mapped_column(String(40), default="text")
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    status: Mapped[str] = mapped_column(String(40), default="pending")
    sent_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)
    error_log: Mapped[dict | None] = mapped_column(JSON, nullable=True)
