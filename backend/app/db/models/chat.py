from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDTimestampMixin


class Chat(Base, UUIDTimestampMixin):
    __tablename__ = "chats"
    __table_args__ = (UniqueConstraint("instance_id", "remote_jid", name="uq_chats_instance_remote_jid"),)

    instance_id: Mapped[str] = mapped_column(ForeignKey("instances.id", ondelete="CASCADE"), index=True)
    remote_jid: Mapped[str] = mapped_column(String(180))
    chat_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    unread_count: Mapped[int] = mapped_column(Integer, default=0)
    is_group: Mapped[bool] = mapped_column(Boolean, default=False)
    synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
