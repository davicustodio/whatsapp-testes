from typing import Annotated, Any

from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_embedding_service_dep, get_provider_dep
from app.services.sync_service import SyncService

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/evolution")
async def evolution_webhook(
    payload: dict[str, Any],
    session: Annotated[AsyncSession, Depends(get_db)],
    provider=Depends(get_provider_dep),
    embedding_service=Depends(get_embedding_service_dep),
    x_event_name: str | None = Header(default=None, alias="x-event-name"),
) -> dict[str, bool]:
    event = x_event_name or payload.get("event") or payload.get("eventType") or ""
    service = SyncService(session=session, provider=provider, embedding_service=embedding_service)
    await service.process_webhook(event=event, payload=payload)
    return {"ok": True}
