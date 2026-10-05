from typing import Annotated

from fastapi import APIRouter, Depends

from club_service.api.dependencies import SessionDependency
from club_service.api.dependencies.auth import get_current_user, require_employee
from club_service.core.errors import NotFoundError
from club_service.infrastructure.models import User
from club_service.repositories.users import get_user_by_id
from club_service.schemas.users import UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
def get_me(current_user: Annotated[User, Depends(get_current_user)]) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    session: SessionDependency,
    _: Annotated[User, Depends(require_employee)],
) -> UserResponse:
    user = get_user_by_id(session, user_id)
    if user is None:
        raise NotFoundError("User not found")
    return UserResponse.model_validate(user)
