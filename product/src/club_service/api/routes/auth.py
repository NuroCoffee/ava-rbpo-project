from fastapi import APIRouter, status

from club_service.api.dependencies import SessionDependency
from club_service.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from club_service.schemas.users import UserResponse
from club_service.services.auth import authenticate_user, register_client

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(data: RegisterRequest, session: SessionDependency) -> UserResponse:
    return UserResponse.model_validate(register_client(session, data.email, data.password))


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, session: SessionDependency) -> TokenResponse:
    token = authenticate_user(session, data.email, data.password)
    return TokenResponse(access_token=token)
