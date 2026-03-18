from datetime import datetime

from pydantic import BaseModel


class InstanceOut(BaseModel):
    id: str
    instance_name: str
    phone_number: str | None = None
    profile_name: str | None = None
    status: str | None = None
    provider: str
    synced_at: datetime | None = None


class ContactOut(BaseModel):
    id: str
    remote_jid: str
    push_name: str | None = None
    phone_number: str | None = None
    is_business: bool = False


class ChatOut(BaseModel):
    id: str
    remote_jid: str
    chat_name: str | None = None
    is_group: bool = False
    unread_count: int = 0
    last_message_at: datetime | None = None


class MessageOut(BaseModel):
    id: str
    message_external_id: str
    remote_jid: str
    from_me: bool
    sender_name: str | None = None
    content: str | None = None
    message_type: str
    timestamp: datetime


class SyncResponse(BaseModel):
    instance_name: str
    contacts_count: int
    chats_count: int
    messages_count: int
    embedded_count: int
