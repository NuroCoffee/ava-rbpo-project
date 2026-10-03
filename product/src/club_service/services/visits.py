from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from club_service.core.errors import ConflictError, NotFoundError
from club_service.infrastructure.models import Visit
from club_service.repositories.memberships import get_current_membership
from club_service.repositories.users import get_user_by_id
from club_service.repositories.visits import (
    get_visit_by_idempotency_key,
    list_visits_for_user,
)


def _ensure_same_operation(visit: Visit, user_id: int) -> Visit:
    if visit.membership.user_id != user_id:
        raise ConflictError("Idempotency key was already used for another operation")
    return visit


def register_visit(
    session: Session,
    user_id: int,
    registered_by: int,
    idempotency_key: UUID,
) -> Visit:
    existing = get_visit_by_idempotency_key(session, idempotency_key)
    if existing is not None:
        return _ensure_same_operation(existing, user_id)

    user = get_user_by_id(session, user_id)
    if user is None or not user.is_active:
        raise NotFoundError("Active user not found")

    now = datetime.now(UTC)
    membership = get_current_membership(session, user_id, now, for_update=True)
    if membership is None:
        raise ConflictError("User does not have a valid active membership")

    existing = get_visit_by_idempotency_key(session, idempotency_key)
    if existing is not None:
        return _ensure_same_operation(existing, user_id)
    if membership.remaining_visits is not None:
        if membership.remaining_visits <= 0:
            raise ConflictError("Membership has no remaining visits")
        membership.remaining_visits -= 1

    visit = Visit(
        membership=membership,
        registered_by=registered_by,
        visited_at=now,
        idempotency_key=idempotency_key,
    )
    session.add(visit)
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        existing = get_visit_by_idempotency_key(session, idempotency_key)
        if existing is not None:
            return _ensure_same_operation(existing, user_id)
        raise ConflictError("Could not register visit") from error
    session.refresh(visit)
    return visit


def get_user_visits(session: Session, user_id: int) -> list[Visit]:
    if get_user_by_id(session, user_id) is None:
        raise NotFoundError("User not found")
    return list_visits_for_user(session, user_id)
