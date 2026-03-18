from typing import Any

from app.providers.base import (
    ProviderChat,
    ProviderContact,
    ProviderInstance,
    ProviderMessage,
    WhatsAppProvider,
)


class MetaCloudProvider(WhatsAppProvider):
    async def list_instances(self) -> list[ProviderInstance]:
        raise NotImplementedError("MetaCloudProvider ainda nao foi implementado.")

    async def get_contacts(self, instance_name: str) -> list[ProviderContact]:
        raise NotImplementedError("MetaCloudProvider ainda nao foi implementado.")

    async def get_chats(self, instance_name: str) -> list[ProviderChat]:
        raise NotImplementedError("MetaCloudProvider ainda nao foi implementado.")

    async def get_messages(
        self,
        instance_name: str,
        chat_jid: str | None = None,
        max_pages: int = 0,
    ) -> list[ProviderMessage]:
        raise NotImplementedError("MetaCloudProvider ainda nao foi implementado.")

    async def send_text(self, instance_name: str, number: str, text: str) -> dict[str, Any]:
        raise NotImplementedError("MetaCloudProvider ainda nao foi implementado.")
