from sqlalchemy import select
from sqlalchemy.orm import Session

from club_service.infrastructure.models import MembershipPlan


def get_plan_by_id(session: Session, plan_id: int) -> MembershipPlan | None:
    return session.get(MembershipPlan, plan_id)


def list_active_plans(session: Session) -> list[MembershipPlan]:
    statement = (
        select(MembershipPlan).where(MembershipPlan.is_active.is_(True)).order_by(MembershipPlan.id)
    )
    return list(session.scalars(statement))
