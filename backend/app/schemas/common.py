from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class MessageResponse(BaseModel):
    message: str


class HealthResponse(BaseModel):
    status: str
    version: str


class PaginationMeta(BaseModel):
    page: int
    limit: int
    total: int


class TimestampResponse(BaseModel):
    created_at: datetime
    updated_at: datetime


class IDResponse(BaseModel):
    id: UUID
