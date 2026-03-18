from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth_router, instances_router, webhooks_router
from app.core.config import get_settings
from app.services.scheduler_service import scheduler_service

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    scheduler_service.start()
    await scheduler_service.restore_pending_jobs()
    yield


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth_router, prefix="/api")
app.include_router(instances_router, prefix="/api")
app.include_router(webhooks_router, prefix="/api")
