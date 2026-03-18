import hashlib
from datetime import UTC, datetime
from typing import Any

import httpx

from app.providers.base import (
    ProviderChat,
    ProviderContact,
    ProviderInstance,
    ProviderMessage,
    WhatsAppProvider,
)


def _to_phone_number(value: str | None) -> str | None:
    if not value:
        return None
    return value.split("@")[0]


def _to_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, (int, float)):
        # Evolution normalmente envia em segundos, mas algumas versões retornam ms.
        ts = value / 1000 if value > 9_999_999_999 else value
        return datetime.fromtimestamp(ts, tz=UTC)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
        except ValueError:
            pass
    return datetime.now(tz=UTC)


class EvolutionProvider(WhatsAppProvider):
    def __init__(self, base_url: str, api_key: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    async def _request(self, method: str, path: str, json: dict[str, Any] | None = None) -> Any:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["apikey"] = self.api_key

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.request(
                method=method,
                url=f"{self.base_url}{path}",
                headers=headers,
                json=json,
            )
            response.raise_for_status()
            return response.json()

    async def list_instances(self) -> list[ProviderInstance]:
        payload = await self._request("GET", "/instance/fetchInstances")
        items = payload if isinstance(payload, list) else payload.get("instances", [])
        instances: list[ProviderInstance] = []
        for item in items:
            owner = item.get("owner")
            instances.append(
                ProviderInstance(
                    instance_name=item.get("name") or item.get("instanceName") or "",
                    instance_external_id=item.get("id") or item.get("instanceId"),
                    owner_jid=owner,
                    profile_name=item.get("profileName"),
                    profile_pic_url=item.get("profilePictureUrl"),
                    status=item.get("connectionStatus") or item.get("status"),
                    phone_number=_to_phone_number(owner),
                )
            )
        return [instance for instance in instances if instance.instance_name]

    @staticmethod
    def _extract_records(payload: Any, primary_key: str) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]

        if not isinstance(payload, dict):
            return []

        candidate = payload.get(primary_key)
        if isinstance(candidate, list):
            return [item for item in candidate if isinstance(item, dict)]
        if isinstance(candidate, dict):
            records = candidate.get("records")
            if isinstance(records, list):
                return [item for item in records if isinstance(item, dict)]

        data = payload.get("data")
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        if isinstance(data, dict):
            records = data.get("records")
            if isinstance(records, list):
                return [item for item in records if isinstance(item, dict)]

        records = payload.get("records")
        if isinstance(records, list):
            return [item for item in records if isinstance(item, dict)]

        return []

    @staticmethod
    def _extract_pages(payload: Any, primary_key: str) -> int:
        if not isinstance(payload, dict):
            return 1
        candidate = payload.get(primary_key)
        if isinstance(candidate, dict):
            pages = candidate.get("pages")
            if isinstance(pages, int) and pages > 0:
                return pages
        return 1

    async def get_contacts(self, instance_name: str) -> list[ProviderContact]:
        payload = await self._request("POST", f"/chat/findContacts/{instance_name}", json={})
        items = self._extract_records(payload=payload, primary_key="contacts")
        contacts: list[ProviderContact] = []
        for item in items:
            jid = item.get("id") or item.get("remoteJid")
            if not jid:
                continue
            contacts.append(
                ProviderContact(
                    remote_jid=jid,
                    push_name=item.get("pushName") or item.get("name"),
                    phone_number=_to_phone_number(jid),
                    is_business=bool(item.get("isBusiness", False)),
                )
            )
        return contacts

    async def get_chats(self, instance_name: str) -> list[ProviderChat]:
        payload = await self._request("POST", f"/chat/findChats/{instance_name}", json={})
        items = self._extract_records(payload=payload, primary_key="chats")
        chats: list[ProviderChat] = []
        for item in items:
            jid = item.get("id") or item.get("remoteJid")
            if not jid:
                continue
            chats.append(
                ProviderChat(
                    remote_jid=jid,
                    chat_name=item.get("name") or item.get("subject"),
                    last_message_at=_to_datetime(item.get("conversationTimestamp") or item.get("lastMessageTimestamp")),
                    unread_count=int(item.get("unreadCount", 0) or 0),
                    is_group=jid.endswith("@g.us"),
                )
            )
        return chats

    async def get_messages(
        self,
        instance_name: str,
        chat_jid: str | None = None,
        max_pages: int = 0,
    ) -> list[ProviderMessage]:
        body_base: dict[str, Any] = {}
        if chat_jid:
            body_base = {"where": {"key": {"remoteJid": chat_jid}}}

        payload = await self._request("POST", f"/chat/findMessages/{instance_name}", json=body_base)
        all_items = self._extract_records(payload=payload, primary_key="messages")

        total_pages = self._extract_pages(payload=payload, primary_key="messages")
        if max_pages > 0:
            total_pages = min(total_pages, max_pages)

        for page in range(2, total_pages + 1):
            body_page = {**body_base, "page": page}
            page_payload = await self._request("POST", f"/chat/findMessages/{instance_name}", json=body_page)
            all_items.extend(self._extract_records(payload=page_payload, primary_key="messages"))

        messages: list[ProviderMessage] = []
        for item in all_items:
            key = item.get("key", {})
            remote_jid = key.get("remoteJid") or item.get("remoteJid")
            if not remote_jid:
                continue

            raw_text = (item.get("message", {}).get("conversation")
                        or item.get("message", {}).get("extendedTextMessage", {}).get("text")
                        or item.get("text")
                        or "")
            timestamp = _to_datetime(item.get("messageTimestamp") or item.get("timestamp"))
            external_id = key.get("id") or item.get("id")
            if not external_id:
                hash_source = f"{remote_jid}:{timestamp.isoformat()}:{raw_text}"
                external_id = hashlib.sha1(hash_source.encode("utf-8"), usedforsecurity=False).hexdigest()

            messages.append(
                ProviderMessage(
                    message_external_id=external_id,
                    remote_jid=remote_jid,
                    from_me=bool(key.get("fromMe", False)),
                    sender_jid=key.get("participant"),
                    sender_name=item.get("pushName"),
                    content=raw_text or None,
                    message_type=item.get("messageType") or "text",
                    media_url=item.get("mediaUrl"),
                    media_mimetype=item.get("mimetype"),
                    timestamp=timestamp,
                )
            )
        return messages

    async def send_text(self, instance_name: str, number: str, text: str) -> dict[str, Any]:
        clean_number = "".join(char for char in number if char.isdigit())
        body = {"number": clean_number, "text": text}
        payload = await self._request("POST", f"/message/sendText/{instance_name}", json=body)
        return payload if isinstance(payload, dict) else {"result": payload}
