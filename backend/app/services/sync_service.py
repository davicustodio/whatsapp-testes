import hashlib
from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Select, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.models.chat import Chat
from app.db.models.contact import Contact
from app.db.models.instance import Instance
from app.db.models.message import Message
from app.providers.base import ProviderMessage, WhatsAppProvider
from app.services.embedding_service import EmbeddingService


def _to_phone_number(value: str | None) -> str | None:
    if not value:
        return None
    return value.split("@")[0]


class SyncService:
    MESSAGE_UPSERT_BATCH_SIZE = 1000

    def __init__(
        self,
        session: AsyncSession,
        provider: WhatsAppProvider,
        embedding_service: EmbeddingService,
    ) -> None:
        self.session = session
        self.provider = provider
        self.embedding_service = embedding_service
        self.settings = get_settings()

    async def sync_instance(self, instance_name: str) -> dict[str, int | str]:
        provider_instances = await self.provider.list_instances()
        provider_instance = next(
            (item for item in provider_instances if item.instance_name == instance_name),
            None,
        )

        if provider_instance is None:
            provider_instance = next(
                (item for item in provider_instances if item.phone_number == instance_name),
                None,
            )

        instance_id = await self._upsert_instance(instance_name=instance_name, provider_instance=provider_instance)

        contacts = await self.provider.get_contacts(instance_name)
        chats = await self.provider.get_chats(instance_name)

        await self._upsert_contacts(instance_id=instance_id, contacts=contacts)
        await self._upsert_chats(instance_id=instance_id, chats=chats)

        chat_id_by_jid = await self._fetch_chat_map(instance_id=instance_id)
        provider_messages = await self.provider.get_messages(
            instance_name=instance_name,
            chat_jid=None,
            max_pages=self.settings.evolution_messages_max_pages,
        )
        await self._upsert_messages(
            instance_id=instance_id,
            chat_id_by_jid=chat_id_by_jid,
            provider_messages=provider_messages,
        )
        messages_count = len(provider_messages)

        embedded_count = await self._embed_missing_messages(instance_id)

        await self.session.execute(
            update(Instance)
            .where(Instance.id == instance_id)
            .values(synced_at=datetime.now(tz=UTC))
        )
        await self.session.commit()

        return {
            "instance_name": instance_name,
            "contacts_count": len(contacts),
            "chats_count": len(chats),
            "messages_count": messages_count,
            "embedded_count": embedded_count,
        }

    async def process_webhook(self, event: str, payload: dict[str, Any]) -> None:
        # Eventos suportados para sync incremental.
        if event not in {"MESSAGES_UPSERT", "CONTACTS_UPSERT", "CHATS_UPSERT"}:
            return

        instance_name = (
            payload.get("instance")
            or payload.get("instanceName")
            or payload.get("data", {}).get("instance")
        )
        if not instance_name:
            return

        instance_id = await self._get_instance_id_by_name(instance_name)
        if instance_id is None:
            # Faz bootstrap da instancia caso ainda nao exista localmente.
            sync_result = await self.sync_instance(instance_name)
            instance_id = await self._get_instance_id_by_name(sync_result["instance_name"])
            if instance_id is None:
                return

        if event == "MESSAGES_UPSERT":
            data = payload.get("data") or payload.get("messages") or []
            provider_messages = self._parse_webhook_messages(data)
            chat_id_by_jid = await self._fetch_chat_map(instance_id=instance_id)
            await self._upsert_messages(
                instance_id=instance_id,
                chat_id_by_jid=chat_id_by_jid,
                provider_messages=provider_messages,
            )
            await self._embed_missing_messages(instance_id)
            await self.session.commit()

    async def _upsert_instance(self, instance_name: str, provider_instance: Any | None) -> str:
        values = {
            "instance_name": instance_name,
            "instance_external_id": provider_instance.instance_external_id if provider_instance else None,
            "owner_jid": provider_instance.owner_jid if provider_instance else None,
            "phone_number": provider_instance.phone_number if provider_instance else None,
            "profile_name": provider_instance.profile_name if provider_instance else None,
            "profile_pic_url": provider_instance.profile_pic_url if provider_instance else None,
            "status": provider_instance.status if provider_instance else None,
            "provider": "evolution",
            "synced_at": datetime.now(tz=UTC),
        }
        statement = (
            insert(Instance)
            .values(values)
            .on_conflict_do_update(
                index_elements=[Instance.instance_name],
                set_={
                    "instance_external_id": values["instance_external_id"],
                    "owner_jid": values["owner_jid"],
                    "phone_number": values["phone_number"],
                    "profile_name": values["profile_name"],
                    "profile_pic_url": values["profile_pic_url"],
                    "status": values["status"],
                    "provider": values["provider"],
                    "synced_at": values["synced_at"],
                    "updated_at": datetime.now(tz=UTC),
                },
            )
            .returning(Instance.id)
        )
        result = await self.session.execute(statement)
        return result.scalar_one()

    async def _upsert_contacts(self, instance_id: str, contacts: Iterable[Any]) -> None:
        rows: list[dict[str, Any]] = []
        synced_at = datetime.now(tz=UTC)
        for contact in contacts:
            rows.append(
                {
                    "instance_id": instance_id,
                    "remote_jid": contact.remote_jid,
                    "push_name": contact.push_name,
                    "phone_number": contact.phone_number or _to_phone_number(contact.remote_jid),
                    "profile_pic_url": None,
                    "is_business": contact.is_business,
                    "synced_at": synced_at,
                }
            )
        if not rows:
            return

        statement = insert(Contact).values(rows)
        statement = statement.on_conflict_do_update(
            constraint="uq_contacts_instance_remote_jid",
            set_={
                "push_name": statement.excluded.push_name,
                "phone_number": statement.excluded.phone_number,
                "is_business": statement.excluded.is_business,
                "synced_at": statement.excluded.synced_at,
                "updated_at": datetime.now(tz=UTC),
            },
        )
        await self.session.execute(statement)

    async def _upsert_chats(self, instance_id: str, chats: Iterable[Any]) -> None:
        rows: list[dict[str, Any]] = []
        synced_at = datetime.now(tz=UTC)
        for chat in chats:
            rows.append(
                {
                    "instance_id": instance_id,
                    "remote_jid": chat.remote_jid,
                    "chat_name": chat.chat_name,
                    "last_message_at": chat.last_message_at,
                    "unread_count": chat.unread_count,
                    "is_group": chat.is_group,
                    "synced_at": synced_at,
                }
            )
        if not rows:
            return

        statement = insert(Chat).values(rows)
        statement = statement.on_conflict_do_update(
            constraint="uq_chats_instance_remote_jid",
            set_={
                "chat_name": statement.excluded.chat_name,
                "last_message_at": statement.excluded.last_message_at,
                "unread_count": statement.excluded.unread_count,
                "is_group": statement.excluded.is_group,
                "synced_at": statement.excluded.synced_at,
                "updated_at": datetime.now(tz=UTC),
            },
        )
        await self.session.execute(statement)

    async def _fetch_chat_map(self, instance_id: str) -> dict[str, str]:
        query: Select[tuple[str, str]] = select(Chat.remote_jid, Chat.id).where(Chat.instance_id == instance_id)
        rows = await self.session.execute(query)
        return {remote_jid: chat_id for remote_jid, chat_id in rows.all()}

    async def _upsert_messages(
        self,
        instance_id: str,
        chat_id_by_jid: dict[str, str],
        provider_messages: Iterable[ProviderMessage],
    ) -> None:
        rows: list[dict[str, Any]] = []
        for message in provider_messages:
            external_id = message.message_external_id
            if not external_id:
                hash_source = f"{message.remote_jid}:{message.timestamp.isoformat()}:{message.content or ''}"
                external_id = hashlib.sha1(hash_source.encode("utf-8"), usedforsecurity=False).hexdigest()

            rows.append(
                {
                    "instance_id": instance_id,
                    "chat_id": chat_id_by_jid.get(message.remote_jid),
                    "message_external_id": external_id,
                    "remote_jid": message.remote_jid,
                    "from_me": message.from_me,
                    "sender_jid": message.sender_jid,
                    "sender_name": message.sender_name,
                    "content": message.content,
                    "message_type": message.message_type,
                    "media_url": message.media_url,
                    "media_mimetype": message.media_mimetype,
                    "timestamp": message.timestamp,
                }
            )
        if not rows:
            return

        for start in range(0, len(rows), self.MESSAGE_UPSERT_BATCH_SIZE):
            batch_rows = rows[start : start + self.MESSAGE_UPSERT_BATCH_SIZE]
            statement = insert(Message).values(batch_rows)
            statement = statement.on_conflict_do_update(
                constraint="uq_messages_instance_external",
                set_={
                    "chat_id": statement.excluded.chat_id,
                    "remote_jid": statement.excluded.remote_jid,
                    "from_me": statement.excluded.from_me,
                    "sender_jid": statement.excluded.sender_jid,
                    "sender_name": statement.excluded.sender_name,
                    "content": statement.excluded.content,
                    "message_type": statement.excluded.message_type,
                    "media_url": statement.excluded.media_url,
                    "media_mimetype": statement.excluded.media_mimetype,
                    "timestamp": statement.excluded.timestamp,
                    "updated_at": datetime.now(tz=UTC),
                },
            )
            await self.session.execute(statement)

    async def _embed_missing_messages(self, instance_id: str) -> int:
        embedding_limit = max(1, int(self.settings.embedding_max_per_sync))
        result = await self.session.execute(
            select(Message)
            .where(
                Message.instance_id == instance_id,
                Message.content.is_not(None),
                Message.content != "",
                Message.embedding.is_(None),
            )
            .order_by(Message.timestamp.desc())
            .limit(embedding_limit)
        )
        missing = list(result.scalars().all())
        if not missing:
            return 0

        vectors = await self.embedding_service.embed_texts([msg.content or "" for msg in missing])
        embedded_count = 0
        for message, vector in zip(missing, vectors, strict=False):
            if not vector:
                continue
            message.embedding = vector
            message.embedded_at = datetime.now(tz=UTC)
            embedded_count += 1
        return embedded_count

    async def _get_instance_id_by_name(self, instance_name: str) -> str | None:
        result = await self.session.execute(
            select(Instance.id).where(Instance.instance_name == instance_name)
        )
        return result.scalar_one_or_none()

    def _parse_webhook_messages(self, payload_data: Any) -> list[ProviderMessage]:
        items = payload_data if isinstance(payload_data, list) else [payload_data]
        parsed: list[ProviderMessage] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            key = item.get("key", {})
            remote_jid = key.get("remoteJid") or item.get("remoteJid")
            if not remote_jid:
                continue
            timestamp_raw = item.get("messageTimestamp") or item.get("timestamp") or datetime.now(tz=UTC).timestamp()
            timestamp = datetime.fromtimestamp(float(timestamp_raw), tz=UTC)
            text = (
                item.get("message", {}).get("conversation")
                or item.get("message", {}).get("extendedTextMessage", {}).get("text")
                or item.get("text")
            )
            external_id = key.get("id")
            if not external_id:
                hash_source = f"{remote_jid}:{timestamp.isoformat()}:{text or ''}"
                external_id = hashlib.sha1(hash_source.encode("utf-8"), usedforsecurity=False).hexdigest()
            parsed.append(
                ProviderMessage(
                    message_external_id=external_id,
                    remote_jid=remote_jid,
                    from_me=bool(key.get("fromMe", False)),
                    sender_jid=key.get("participant"),
                    sender_name=item.get("pushName"),
                    content=text,
                    message_type=item.get("messageType", "text"),
                    media_url=item.get("mediaUrl"),
                    media_mimetype=item.get("mimetype"),
                    timestamp=timestamp,
                )
            )
        return parsed
