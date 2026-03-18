from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDTimestampMixin


class Instance(Base, UUIDTimestampMixin):
    __tablename__ = "instances"

    instance_name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    instance_external_id: Mapped[str | None] = mapped_column(String(150), nullable=True)
    owner_jid: Mapped[str | None] = mapped_column(String(150), nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String(30), nullable=True)
    profile_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    profile_pic_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    status: Mapped[str | None] = mapped_column(String(40), nullable=True)
    provider: Mapped[str] = mapped_column(String(30), default="evolution")
    synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
