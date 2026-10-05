from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from club_service.core.errors import AuthenticationError, ConflictError
from club_service.core.security import create_access_token, hash_password, verify_password
from club_service.domain.enums import UserRole
from club_service.infrastructure.models import User
from club_service.repositories.users import get_user_by_email


def register_client(session: Session, email: str, password: str) -> User:
    normalized_email = email.strip().lower()
    if get_user_by_email(session, normalized_email) is not None:
        raise ConflictError("A user with this email already exists")

    user = User(
        email=normalized_email,
        password_hash=hash_password(password),
        role=UserRole.CLIENT,
    )
    session.add(user)
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        raise ConflictError("A user with this email already exists") from error
    session.refresh(user)
    return user


def authenticate_user(session: Session, email: str, password: str) -> str:
    user = get_user_by_email(session, email.strip().lower())
    if user is None or not user.is_active or not verify_password(password, user.password_hash):
        raise AuthenticationError("Invalid email or password")
    return create_access_token(user.id)


def create_privileged_user(
    session: Session,
    email: str,
    password: str,
    role: UserRole,
) -> User:
    normalized_email = email.strip().lower()
    if get_user_by_email(session, normalized_email) is not None:
        raise ConflictError("A user with this email already exists")
    user = User(
        email=normalized_email,
        password_hash=hash_password(password),
        role=role,
    )
    session.add(user)
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        raise ConflictError("A user with this email already exists") from error
    session.refresh(user)
    return user
