from fastapi import APIRouter, HTTPException, status

from app.core.security import create_access_token, verify_auth_password
from app.schemas.auth import LoginRequest, LoginResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest) -> LoginResponse:
    if not verify_auth_password(payload.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Senha invalida.",
        )
    token = create_access_token(subject="ui-user")
    return LoginResponse(access_token=token)
