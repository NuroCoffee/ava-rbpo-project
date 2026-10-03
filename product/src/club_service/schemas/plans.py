from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MembershipPlanCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    duration_days: int = Field(gt=0)
    visits_limit: int | None = Field(default=None, gt=0)
    freeze_days_limit: int = Field(default=0, ge=0)


class MembershipPlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    duration_days: int
    visits_limit: int | None
    freeze_days_limit: int
    is_active: bool
    created_at: datetime
