from typing import Annotated

from fastapi import APIRouter, Depends, status

from club_service.api.dependencies import SessionDependency
from club_service.api.dependencies.auth import require_client, require_employee
from club_service.infrastructure.models import Membership, User
from club_service.schemas.memberships import MembershipCreate, MembershipResponse
from club_service.services.memberships import get_my_membership, issue_membership

router = APIRouter(prefix="/memberships", tags=["memberships"])


def _membership_response(membership: Membership) -> MembershipResponse:
    return MembershipResponse(
        id=membership.id,
        user_id=membership.user_id,
        plan_id=membership.plan_id,
        plan_name=membership.plan.name,
        starts_at=membership.starts_at,
        expires_at=membership.expires_at,
        remaining_visits=membership.remaining_visits,
        status=membership.status,
    )


@router.post("", response_model=MembershipResponse, status_code=status.HTTP_201_CREATED)
def create_membership(
    data: MembershipCreate,
    session: SessionDependency,
    _: Annotated[User, Depends(require_employee)],
) -> MembershipResponse:
    return _membership_response(issue_membership(session, data.user_id, data.plan_id))


@router.get("/me", response_model=MembershipResponse)
def get_own_membership(
    session: SessionDependency,
    current_user: Annotated[User, Depends(require_client)],
) -> MembershipResponse:
    return _membership_response(get_my_membership(session, current_user.id))
