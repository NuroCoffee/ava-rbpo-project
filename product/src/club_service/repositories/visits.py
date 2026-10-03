from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from club_service.infrastructure.models import Membership, Visit


def get_visit_by_idempotency_key(session: Session, key: UUID) -> Visit | None:
    statement = (
        select(Visit)
        .options(joinedload(Visit.membership))
        .where(Visit.idempotency_key == key)
    )
    return session.scalar(statement)


def list_visits_for_user(session: Session, user_id: int) -> list[Visit]:
    statement = (
        select(Visit)
        .join(Visit.membership)
        .where(Membership.user_id == user_id)
        .order_by(Visit.visited_at.desc(), Visit.id.desc())
    )
    return list(session.scalars(statement))
