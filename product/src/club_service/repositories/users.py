from sqlalchemy import select
from sqlalchemy.orm import Session

from club_service.infrastructure.models import User


def get_user_by_id(session: Session, user_id: int, *, for_update: bool = False) -> User | None:
    statement = select(User).where(User.id == user_id)
    if for_update:
        statement = statement.with_for_update()
    return session.scalar(statement)


def get_user_by_email(session: Session, email: str) -> User | None:
    return session.scalar(select(User).where(User.email == email))
