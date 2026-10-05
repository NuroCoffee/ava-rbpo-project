from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from club_service.domain.enums import MembershipStatus


class MembershipCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: int = Field(gt=0)
    plan_id: int = Field(gt=0)


class MembershipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    plan_id: int
    plan_name: str
    starts_at: datetime
    expires_at: datetime
    remaining_visits: int | None
    status: MembershipStatus
