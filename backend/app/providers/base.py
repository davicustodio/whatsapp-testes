from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class ProviderInstance:
    instance_name: str
    instance_external_id: str | None
    owner_jid: str | None
    profile_name: str | None
    profile_pic_url: str | None
    status: str | None
    phone_number: str | None


@dataclass
class ProviderContact:
    remote_jid: str
    push_name: str | None
    phone_number: str | None
    is_business: bool


@dataclass
class ProviderChat:
    remote_jid: str
    chat_name: str | None
    last_message_at: datetime | None
    unread_count: int
    is_group: bool


@dataclass
class ProviderMessage:
    message_external_id: str
    remote_jid: str
    from_me: bool
    sender_jid: str | None
    sender_name: str | None
    content: str | None
    message_type: str
    media_url: str | None
    media_mimetype: str | None
    timestamp: datetime


class WhatsAppProvider(ABC):
    @abstractmethod
    async def list_instances(self) -> list[ProviderInstance]:
        raise NotImplementedError

    @abstractmethod
    async def get_contacts(self, instance_name: str) -> list[ProviderContact]:
        raise NotImplementedError

    @abstractmethod
    async def get_chats(self, instance_name: str) -> list[ProviderChat]:
        raise NotImplementedError

    @abstractmethod
    async def get_messages(
        self,
        instance_name: str,
        chat_jid: str | None = None,
        max_pages: int = 0,
    ) -> list[ProviderMessage]:
        raise NotImplementedError

    @abstractmethod
    async def send_text(self, instance_name: str, number: str, text: str) -> dict[str, Any]:
        raise NotImplementedError
