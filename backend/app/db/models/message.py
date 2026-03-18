from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDTimestampMixin


class Message(Base, UUIDTimestampMixin):
    __tablename__ = "messages"
    __table_args__ = (
        UniqueConstraint("instance_id", "message_external_id", name="uq_messages_instance_external"),
        Index("ix_messages_remote_jid", "remote_jid"),
        Index("ix_messages_timestamp", "timestamp"),
    )

    instance_id: Mapped[str] = mapped_column(ForeignKey("instances.id", ondelete="CASCADE"), index=True)
    chat_id: Mapped[str | None] = mapped_column(ForeignKey("chats.id", ondelete="SET NULL"), nullable=True, index=True)
    message_external_id: Mapped[str] = mapped_column(String(255))
    remote_jid: Mapped[str] = mapped_column(String(180))
    from_me: Mapped[bool] = mapped_column(Boolean, default=False)
    sender_jid: Mapped[str | None] = mapped_column(String(180), nullable=True)
    sender_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    message_type: Mapped[str] = mapped_column(String(40), default="text")
    media_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    media_mimetype: Mapped[str | None] = mapped_column(String(120), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(384), nullable=True)
    embedded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
