from typing import Annotated

from fastapi import APIRouter, Depends, status

from club_service.api.dependencies import SessionDependency
from club_service.api.dependencies.auth import require_admin
from club_service.infrastructure.models import User
from club_service.schemas.plans import MembershipPlanCreate, MembershipPlanResponse
from club_service.services.plans import create_plan, get_active_plan, get_active_plans

router = APIRouter(prefix="/membership-plans", tags=["membership plans"])


@router.get("", response_model=list[MembershipPlanResponse])
def list_plans(session: SessionDependency) -> list[MembershipPlanResponse]:
    return [MembershipPlanResponse.model_validate(plan) for plan in get_active_plans(session)]


@router.post("", response_model=MembershipPlanResponse, status_code=status.HTTP_201_CREATED)
def add_plan(
    data: MembershipPlanCreate,
    session: SessionDependency,
    _: Annotated[User, Depends(require_admin)],
) -> MembershipPlanResponse:
    return MembershipPlanResponse.model_validate(create_plan(session, data))


@router.get("/{plan_id}", response_model=MembershipPlanResponse)
def get_plan(plan_id: int, session: SessionDependency) -> MembershipPlanResponse:
    return MembershipPlanResponse.model_validate(get_active_plan(session, plan_id))
