from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDTimestampMixin


class Contact(Base, UUIDTimestampMixin):
    __tablename__ = "contacts"
    __table_args__ = (UniqueConstraint("instance_id", "remote_jid", name="uq_contacts_instance_remote_jid"),)

    instance_id: Mapped[str] = mapped_column(ForeignKey("instances.id", ondelete="CASCADE"), index=True)
    remote_jid: Mapped[str] = mapped_column(String(180))
    push_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String(30), nullable=True)
    profile_pic_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    is_business: Mapped[bool] = mapped_column(Boolean, default=False)
    synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
