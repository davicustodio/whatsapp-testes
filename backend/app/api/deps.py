from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.session import get_db_session
from app.providers.factory import get_provider
from app.services.embedding_service import get_embedding_service

security = HTTPBearer(auto_error=False)


async def get_db() -> AsyncSession:
    async for session in get_db_session():
        yield session


def get_provider_dep():
    return get_provider()


def get_embedding_service_dep():
    return get_embedding_service()


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> str:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de acesso obrigatorio.",
        )
    payload = decode_access_token(credentials.credentials)
    subject = payload.get("sub")
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido.",
        )
    return str(subject)
