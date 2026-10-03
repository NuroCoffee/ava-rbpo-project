from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from club_service.core.errors import ConflictError, NotFoundError
from club_service.domain.enums import MembershipStatus, UserRole
from club_service.infrastructure.models import Membership
from club_service.repositories.memberships import get_current_membership
from club_service.repositories.plans import get_plan_by_id
from club_service.repositories.users import get_user_by_id


def issue_membership(session: Session, user_id: int, plan_id: int) -> Membership:
    now = datetime.now(UTC)
    user = get_user_by_id(session, user_id, for_update=True)
    if user is None or not user.is_active:
        raise NotFoundError("Active user not found")
    if user.role != UserRole.CLIENT:
        raise ConflictError("Memberships can only be issued to clients")

    plan = get_plan_by_id(session, plan_id)
    if plan is None or not plan.is_active:
        raise NotFoundError("Active membership plan not found")
    if get_current_membership(session, user_id, now) is not None:
        raise ConflictError("User already has an active membership")

    membership = Membership(
        user=user,
        plan=plan,
        starts_at=now,
        expires_at=now + timedelta(days=plan.duration_days),
        remaining_visits=plan.visits_limit,
        status=MembershipStatus.ACTIVE,
    )
    session.add(membership)
    session.commit()
    session.refresh(membership)
    return membership


def get_my_membership(session: Session, user_id: int) -> Membership:
    membership = get_current_membership(session, user_id, datetime.now(UTC))
    if membership is None:
        raise NotFoundError("Active membership not found")
    return membership
