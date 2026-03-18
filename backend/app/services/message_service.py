from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.batch_message import BatchMessage
from app.db.models.instance import Instance
from app.db.models.scheduled_message import ScheduledMessage
from app.providers.base import WhatsAppProvider
from app.services.scheduler_service import scheduler_service


class MessageService:
    def __init__(self, session: AsyncSession, provider: WhatsAppProvider) -> None:
        self.session = session
        self.provider = provider

    async def send_single(self, instance_name: str, number: str, text: str) -> dict:
        return await self.provider.send_text(instance_name=instance_name, number=number, text=text)

    async def send_batch(self, instance_name: str, recipients: list[str], text: str) -> dict:
        instance_id = await self._resolve_instance_id(instance_name)
        sent = 0
        failed = 0
        errors: list[dict] = []

        for recipient in recipients:
            try:
                await self.provider.send_text(instance_name=instance_name, number=recipient, text=text)
                sent += 1
            except Exception as exc:  # noqa: BLE001
                failed += 1
                errors.append({"recipient": recipient, "error": str(exc)})

        batch_row = BatchMessage(
            instance_id=instance_id,
            recipients=[{"number": recipient} for recipient in recipients],
            content=text,
            message_type="text",
            status="completed" if failed == 0 else "failed",
            total_count=len(recipients),
            sent_count=sent,
            failed_count=failed,
        )
        self.session.add(batch_row)
        await self.session.commit()

        return {
            "batch_id": batch_row.id,
            "total": len(recipients),
            "sent": sent,
            "failed": failed,
            "errors": errors,
        }

    async def schedule_message(
        self,
        instance_name: str,
        recipients: list[str],
        text: str,
        scheduled_at: datetime,
    ) -> ScheduledMessage:
        instance_id = await self._resolve_instance_id(instance_name)
        row = ScheduledMessage(
            instance_id=instance_id,
            recipients=[{"number": recipient} for recipient in recipients],
            content=text,
            message_type="text",
            scheduled_at=scheduled_at.astimezone(UTC),
            status="pending",
        )
        self.session.add(row)
        await self.session.commit()
        await self.session.refresh(row)

        scheduler_service.add_job(scheduled_message_id=row.id, run_at=row.scheduled_at)
        return row

    async def list_scheduled(self, instance_name: str) -> list[ScheduledMessage]:
        instance_id = await self._resolve_instance_id(instance_name)
        result = await self.session.execute(
            select(ScheduledMessage)
            .where(ScheduledMessage.instance_id == instance_id)
            .order_by(ScheduledMessage.scheduled_at.desc())
        )
        return list(result.scalars().all())

    async def cancel_scheduled(self, scheduled_id: str) -> bool:
        result = await self.session.execute(
            select(ScheduledMessage).where(ScheduledMessage.id == scheduled_id)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return False
        if row.status != "pending":
            return False

        row.status = "cancelled"
        await self.session.commit()
        await scheduler_service.cancel_job(scheduled_id)
        return True

    async def _resolve_instance_id(self, instance_name: str) -> str:
        result = await self.session.execute(
            select(Instance.id).where(Instance.instance_name == instance_name)
        )
        instance_id = result.scalar_one_or_none()
        if instance_id:
            return instance_id

        new_instance = Instance(
            instance_name=instance_name,
            provider="evolution",
        )
        self.session.add(new_instance)
        await self.session.flush()
        return new_instance.id
