from datetime import UTC, datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from app.db.models.instance import Instance
from app.db.models.scheduled_message import ScheduledMessage
from app.db.session import SessionLocal
from app.providers.factory import get_provider


class SchedulerService:
    def __init__(self) -> None:
        self.scheduler = AsyncIOScheduler(timezone="UTC")
        self.started = False

    def start(self) -> None:
        if self.started:
            return
        self.scheduler.start()
        self.started = True

    async def restore_pending_jobs(self) -> None:
        async with SessionLocal() as session:
            result = await session.execute(
                select(ScheduledMessage).where(ScheduledMessage.status == "pending")
            )
            for job in result.scalars().all():
                self._register_job(job.id, job.scheduled_at)

    def _register_job(self, scheduled_message_id: str, run_at: datetime) -> None:
        self.scheduler.add_job(
            func=self.execute_scheduled_message,
            trigger="date",
            run_date=run_at,
            id=f"scheduled:{scheduled_message_id}",
            args=[scheduled_message_id],
            replace_existing=True,
        )

    def add_job(self, scheduled_message_id: str, run_at: datetime) -> None:
        self._register_job(scheduled_message_id, run_at)

    async def cancel_job(self, scheduled_message_id: str) -> None:
        job_id = f"scheduled:{scheduled_message_id}"
        if self.scheduler.get_job(job_id):
            self.scheduler.remove_job(job_id)

    async def execute_scheduled_message(self, scheduled_message_id: str) -> None:
        async with SessionLocal() as session:
            result = await session.execute(
                select(ScheduledMessage).where(ScheduledMessage.id == scheduled_message_id)
            )
            scheduled = result.scalar_one_or_none()
            if scheduled is None or scheduled.status != "pending":
                return
            if scheduled.scheduled_at > datetime.now(tz=UTC):
                return

            instance_result = await session.execute(
                select(Instance).where(Instance.id == scheduled.instance_id)
            )
            instance = instance_result.scalar_one_or_none()
            if instance is None:
                scheduled.status = "failed"
                scheduled.error_log = {"errors": [{"error": "Instancia nao encontrada"}]}
                await session.commit()
                return

            provider = get_provider()
            sent_count = 0
            failed_count = 0
            errors: list[dict] = []

            scheduled.status = "processing"
            await session.flush()

            for recipient in scheduled.recipients:
                number = recipient.get("number") or recipient.get("jid") or recipient.get("phone")
                if not number:
                    failed_count += 1
                    errors.append({"recipient": recipient, "error": "Numero invalido"})
                    continue
                try:
                    await provider.send_text(
                        instance_name=instance.instance_name,
                        number=number,
                        text=scheduled.content,
                    )
                    sent_count += 1
                except Exception as exc:  # noqa: BLE001
                    failed_count += 1
                    errors.append({"recipient": recipient, "error": str(exc)})

            scheduled.sent_count = sent_count
            scheduled.failed_count = failed_count
            scheduled.error_log = {"errors": errors} if errors else None
            scheduled.status = "completed" if failed_count == 0 else "failed"
            await session.commit()


scheduler_service = SchedulerService()
