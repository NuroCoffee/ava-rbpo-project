from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from club_service.domain.enums import MembershipStatus
from club_service.infrastructure.models import Membership


def get_current_membership(
    session: Session,
    user_id: int,
    now: datetime,
    *,
    for_update: bool = False,
) -> Membership | None:
    statement = (
        select(Membership)
        .options(joinedload(Membership.plan))
        .where(
            Membership.user_id == user_id,
            Membership.status == MembershipStatus.ACTIVE,
            Membership.starts_at <= now,
            Membership.expires_at >= now,
        )
        .order_by(Membership.expires_at.desc())
        .limit(1)
    )
    if for_update:
        statement = statement.with_for_update(of=Membership)
    return session.scalar(statement)
