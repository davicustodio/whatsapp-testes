from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_embedding_service_dep, get_provider_dep
from app.db.models.chat import Chat
from app.db.models.contact import Contact
from app.db.models.instance import Instance
from app.db.models.message import Message
from app.schemas.domain import ChatOut, ContactOut, InstanceOut, MessageOut, SyncResponse
from app.schemas.message import (
    BatchSendRequest,
    ScheduleMessageRequest,
    SemanticSearchRequest,
    SemanticSearchResponse,
    SendMessageRequest,
)
from app.services.llm_service import LLMService
from app.services.message_service import MessageService
from app.services.search_service import SearchService
from app.services.sync_service import SyncService

router = APIRouter(prefix="/instances", tags=["instances"])


def _normalize_number(raw: str) -> str:
    return "".join(ch for ch in raw if ch.isdigit())


async def _get_instance_or_404(session: AsyncSession, instance_name: str) -> Instance:
    result = await session.execute(
        select(Instance).where(Instance.instance_name == instance_name)
    )
    instance = result.scalar_one_or_none()
    if instance is None:
        raise HTTPException(status_code=404, detail="Instancia nao encontrada no banco local.")
    return instance


@router.get("/live")
async def list_live_instances(
    _: Annotated[str, Depends(get_current_user)],
    provider=Depends(get_provider_dep),
) -> list[dict[str, Any]]:
    try:
        instances = await provider.list_instances()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Falha ao consultar Evolution API: {exc}",
        ) from exc
    return [
        {
            "instance_name": item.instance_name,
            "phone_number": item.phone_number,
            "profile_name": item.profile_name,
            "status": item.status,
            "owner_jid": item.owner_jid,
        }
        for item in instances
    ]


@router.get("", response_model=list[InstanceOut])
async def list_local_instances(
    _: Annotated[str, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[InstanceOut]:
    result = await session.execute(select(Instance).order_by(Instance.created_at.desc()))
    rows = result.scalars().all()
    return [
        InstanceOut(
            id=row.id,
            instance_name=row.instance_name,
            phone_number=row.phone_number,
            profile_name=row.profile_name,
            status=row.status,
            provider=row.provider,
            synced_at=row.synced_at,
        )
        for row in rows
    ]


@router.post("/{instance_name}/sync", response_model=SyncResponse)
async def sync_instance(
    instance_name: str,
    _: Annotated[str, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    provider=Depends(get_provider_dep),
    embedding_service=Depends(get_embedding_service_dep),
) -> SyncResponse:
    service = SyncService(session=session, provider=provider, embedding_service=embedding_service)
    try:
        result = await service.sync_instance(instance_name=instance_name)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Falha ao sincronizar dados da instancia: {exc}",
        ) from exc
    return SyncResponse(**result)


@router.get("/{instance_name}/contacts", response_model=list[ContactOut])
async def list_contacts(
    instance_name: str,
    _: Annotated[str, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[ContactOut]:
    instance = await _get_instance_or_404(session, instance_name)
    result = await session.execute(
        select(Contact)
        .where(Contact.instance_id == instance.id)
        .order_by(Contact.push_name.asc().nullslast(), Contact.phone_number.asc().nullslast())
    )
    rows = result.scalars().all()
    return [
        ContactOut(
            id=row.id,
            remote_jid=row.remote_jid,
            push_name=row.push_name,
            phone_number=row.phone_number,
            is_business=row.is_business,
        )
        for row in rows
    ]


@router.get("/{instance_name}/chats", response_model=list[ChatOut])
async def list_chats(
    instance_name: str,
    _: Annotated[str, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> list[ChatOut]:
    instance = await _get_instance_or_404(session, instance_name)
    result = await session.execute(
        select(Chat)
        .where(Chat.instance_id == instance.id)
        .order_by(Chat.last_message_at.desc().nullslast())
    )
    rows = result.scalars().all()
    return [
        ChatOut(
            id=row.id,
            remote_jid=row.remote_jid,
            chat_name=row.chat_name,
            is_group=row.is_group,
            unread_count=row.unread_count,
            last_message_at=row.last_message_at,
        )
        for row in rows
    ]


@router.get("/{instance_name}/messages", response_model=list[MessageOut])
async def list_messages(
    instance_name: str,
    chat_jid: str = Query(default=""),
    _: Annotated[str, Depends(get_current_user)] = "",
    session: Annotated[AsyncSession, Depends(get_db)] = None,
) -> list[MessageOut]:
    assert session is not None
    instance = await _get_instance_or_404(session, instance_name)
    stmt = select(Message).where(Message.instance_id == instance.id)
    if chat_jid:
        stmt = stmt.where(Message.remote_jid == chat_jid)
    stmt = stmt.order_by(Message.timestamp.asc()).limit(1000)
    result = await session.execute(stmt)
    rows = result.scalars().all()
    return [
        MessageOut(
            id=row.id,
            message_external_id=row.message_external_id,
            remote_jid=row.remote_jid,
            from_me=row.from_me,
            sender_name=row.sender_name,
            content=row.content,
            message_type=row.message_type,
            timestamp=row.timestamp,
        )
        for row in rows
    ]


@router.post("/{instance_name}/messages/send")
async def send_message(
    instance_name: str,
    payload: SendMessageRequest,
    _: Annotated[str, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    provider=Depends(get_provider_dep),
) -> dict[str, Any]:
    service = MessageService(session=session, provider=provider)
    try:
        result = await service.send_single(
            instance_name=instance_name,
            number=_normalize_number(payload.number),
            text=payload.text,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Falha ao enviar mensagem: {exc}",
        ) from exc
    return {"ok": True, "result": result}


@router.post("/{instance_name}/messages/batch")
async def send_batch(
    instance_name: str,
    payload: BatchSendRequest,
    _: Annotated[str, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    provider=Depends(get_provider_dep),
) -> dict[str, Any]:
    service = MessageService(session=session, provider=provider)
    normalized_recipients = [_normalize_number(item) for item in payload.recipients]
    try:
        result = await service.send_batch(
            instance_name=instance_name,
            recipients=normalized_recipients,
            text=payload.text,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Falha no envio em lote: {exc}",
        ) from exc
    return {"ok": True, **result}


@router.post("/{instance_name}/messages/schedule")
async def schedule_message(
    instance_name: str,
    payload: ScheduleMessageRequest,
    _: Annotated[str, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    provider=Depends(get_provider_dep),
) -> dict[str, Any]:
    if payload.scheduled_at <= datetime.now(payload.scheduled_at.tzinfo):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A data/hora de agendamento deve ser futura.",
        )
    service = MessageService(session=session, provider=provider)
    row = await service.schedule_message(
        instance_name=instance_name,
        recipients=[_normalize_number(item) for item in payload.recipients],
        text=payload.text,
        scheduled_at=payload.scheduled_at,
    )
    return {
        "id": row.id,
        "status": row.status,
        "scheduled_at": row.scheduled_at,
        "recipients": row.recipients,
    }


@router.get("/{instance_name}/messages/scheduled")
async def list_scheduled(
    instance_name: str,
    _: Annotated[str, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    provider=Depends(get_provider_dep),
) -> list[dict[str, Any]]:
    service = MessageService(session=session, provider=provider)
    rows = await service.list_scheduled(instance_name=instance_name)
    return [
        {
            "id": row.id,
            "status": row.status,
            "scheduled_at": row.scheduled_at,
            "recipients": row.recipients,
            "content": row.content,
            "sent_count": row.sent_count,
            "failed_count": row.failed_count,
        }
        for row in rows
    ]


@router.delete("/scheduled/{scheduled_id}")
async def cancel_scheduled(
    scheduled_id: str,
    _: Annotated[str, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    provider=Depends(get_provider_dep),
) -> dict[str, Any]:
    service = MessageService(session=session, provider=provider)
    ok = await service.cancel_scheduled(scheduled_id=scheduled_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Agendamento nao encontrado ou nao pode ser cancelado.")
    return {"ok": True}


@router.post("/{instance_name}/search", response_model=SemanticSearchResponse)
async def semantic_search(
    instance_name: str,
    payload: SemanticSearchRequest,
    _: Annotated[str, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    embedding_service=Depends(get_embedding_service_dep),
) -> SemanticSearchResponse:
    service = SearchService(
        session=session,
        embedding_service=embedding_service,
        llm_service=LLMService(),
    )
    results, rag_answer = await service.semantic_search(
        instance_name=instance_name,
        query=payload.query,
        limit=payload.limit,
    )
    return SemanticSearchResponse(results=results, rag_answer=rag_answer)
