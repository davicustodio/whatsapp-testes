from datetime import datetime

from pydantic import BaseModel, Field


class SendMessageRequest(BaseModel):
    number: str = Field(min_length=8, max_length=30)
    text: str = Field(min_length=1, max_length=4096)


class BatchSendRequest(BaseModel):
    recipients: list[str] = Field(min_length=1)
    text: str = Field(min_length=1, max_length=4096)


class ScheduleMessageRequest(BaseModel):
    recipients: list[str] = Field(min_length=1)
    text: str = Field(min_length=1, max_length=4096)
    scheduled_at: datetime


class SemanticSearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=2048)
    limit: int = Field(default=10, ge=1, le=30)


class SemanticSearchResult(BaseModel):
    message_id: str
    remote_jid: str
    content: str | None
    timestamp: datetime
    score: float


class SemanticSearchResponse(BaseModel):
    results: list[SemanticSearchResult]
    rag_answer: str | None = None
