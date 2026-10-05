from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from club_service.core.errors import ConflictError, NotFoundError
from club_service.infrastructure.models import MembershipPlan
from club_service.repositories.plans import get_plan_by_id, list_active_plans
from club_service.schemas.plans import MembershipPlanCreate


def create_plan(session: Session, data: MembershipPlanCreate) -> MembershipPlan:
    plan = MembershipPlan(**data.model_dump())
    session.add(plan)
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        raise ConflictError("A membership plan with this name already exists") from error
    session.refresh(plan)
    return plan


def get_active_plan(session: Session, plan_id: int) -> MembershipPlan:
    plan = get_plan_by_id(session, plan_id)
    if plan is None or not plan.is_active:
        raise NotFoundError("Active membership plan not found")
    return plan


def get_active_plans(session: Session) -> list[MembershipPlan]:
    return list_active_plans(session)
