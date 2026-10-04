from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from club_service.api.dependencies import SessionDependency
from club_service.core.security import decode_access_token
from club_service.domain.enums import UserRole
from club_service.infrastructure.models import User
from club_service.repositories.users import get_user_by_id

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    session: SessionDependency,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _authentication_error()
    user_id = decode_access_token(credentials.credentials)
    user = get_user_by_id(session, user_id) if user_id is not None else None
    if user is None or not user.is_active:
        raise _authentication_error()
    return user


def require_client(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if current_user.role != UserRole.CLIENT:
        raise HTTPException(status_code=403, detail="Client role is required")
    return current_user


def require_employee(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if current_user.role not in {UserRole.EMPLOYEE, UserRole.ADMIN}:
        raise HTTPException(status_code=403, detail="Employee role is required")
    return current_user


def require_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Administrator role is required")
    return current_user


def _authentication_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing access token",
        headers={"WWW-Authenticate": "Bearer"},
    )
