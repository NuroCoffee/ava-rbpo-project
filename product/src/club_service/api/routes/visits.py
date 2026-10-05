from typing import Annotated

from fastapi import APIRouter, Depends, status

from club_service.api.dependencies import SessionDependency
from club_service.api.dependencies.auth import require_client, require_employee
from club_service.infrastructure.models import User
from club_service.schemas.visits import VisitCreate, VisitResponse
from club_service.services.visits import get_user_visits, register_visit

router = APIRouter(tags=["visits"])


@router.post("/visits", response_model=VisitResponse, status_code=status.HTTP_201_CREATED)
def create_visit(
    data: VisitCreate,
    session: SessionDependency,
    current_user: Annotated[User, Depends(require_employee)],
) -> VisitResponse:
    visit = register_visit(
        session,
        data.user_id,
        current_user.id,
        data.idempotency_key,
    )
    return VisitResponse.model_validate(visit)


@router.get("/visits/me", response_model=list[VisitResponse])
def list_my_visits(
    session: SessionDependency,
    current_user: Annotated[User, Depends(require_client)],
) -> list[VisitResponse]:
    return [
        VisitResponse.model_validate(visit) for visit in get_user_visits(session, current_user.id)
    ]


@router.get("/users/{user_id}/visits", response_model=list[VisitResponse])
def list_client_visits(
    user_id: int,
    session: SessionDependency,
    _: Annotated[User, Depends(require_employee)],
) -> list[VisitResponse]:
    return [VisitResponse.model_validate(visit) for visit in get_user_visits(session, user_id)]
