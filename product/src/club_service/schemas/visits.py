from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class VisitCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: int = Field(gt=0)
    idempotency_key: UUID


class VisitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    membership_id: int
    registered_by: int
    visited_at: datetime
    idempotency_key: UUID
