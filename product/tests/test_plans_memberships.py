from collections.abc import Callable

from sqlalchemy.orm import Session, sessionmaker

from club_service.domain.enums import UserRole
from club_service.infrastructure.models import MembershipPlan, User
from tests.conftest import ApiClient

PLAN_PAYLOAD = {
    "name": "Standard",
    "duration_days": 30,
    "visits_limit": 12,
    "freeze_days_limit": 7,
}


def test_active_plans_are_public(api_client: ApiClient) -> None:
    response = api_client.get("/api/v1/membership-plans")

    assert response.status_code == 200
    assert response.json() == []


def test_client_cannot_create_plan(
    api_client: ApiClient,
    user_factory: Callable[[str, UserRole], User],
    auth_headers: Callable[[User], dict[str, str]],
) -> None:
    client = user_factory("client@example.com", UserRole.CLIENT)

    response = api_client.post(
        "/api/v1/membership-plans",
        json=PLAN_PAYLOAD,
        headers=auth_headers(client),
    )

    assert response.status_code == 403


def test_employee_cannot_create_plan(
    api_client: ApiClient,
    user_factory: Callable[[str, UserRole], User],
    auth_headers: Callable[[User], dict[str, str]],
) -> None:
    employee = user_factory("employee@example.com", UserRole.EMPLOYEE)

    response = api_client.post(
        "/api/v1/membership-plans",
        json=PLAN_PAYLOAD,
        headers=auth_headers(employee),
    )

    assert response.status_code == 403


def test_admin_can_create_plan(
    api_client: ApiClient,
    user_factory: Callable[[str, UserRole], User],
    auth_headers: Callable[[User], dict[str, str]],
) -> None:
    admin = user_factory("admin@example.com", UserRole.ADMIN)

    response = api_client.post(
        "/api/v1/membership-plans",
        json=PLAN_PAYLOAD,
        headers=auth_headers(admin),
    )

    assert response.status_code == 201
    assert response.json()["visits_limit"] == 12


def test_invalid_plan_limits_are_rejected(
    api_client: ApiClient,
    user_factory: Callable[[str, UserRole], User],
    auth_headers: Callable[[User], dict[str, str]],
) -> None:
    admin = user_factory("admin@example.com", UserRole.ADMIN)

    invalid_duration = api_client.post(
        "/api/v1/membership-plans",
        json={**PLAN_PAYLOAD, "duration_days": 0},
        headers=auth_headers(admin),
    )
    invalid_visits = api_client.post(
        "/api/v1/membership-plans",
        json={**PLAN_PAYLOAD, "visits_limit": 0},
        headers=auth_headers(admin),
    )

    assert invalid_duration.status_code == 422
    assert invalid_visits.status_code == 422


def test_employee_issues_membership_and_client_sees_it(
    api_client: ApiClient,
    session_factory: sessionmaker[Session],
    user_factory: Callable[[str, UserRole], User],
    auth_headers: Callable[[User], dict[str, str]],
) -> None:
    employee = user_factory("employee@example.com", UserRole.EMPLOYEE)
    client = user_factory("client@example.com", UserRole.CLIENT)
    with session_factory() as session:
        plan = MembershipPlan(**PLAN_PAYLOAD)
        session.add(plan)
        session.commit()
        plan_id = plan.id

    response = api_client.post(
        "/api/v1/memberships",
        json={"user_id": client.id, "plan_id": plan_id},
        headers=auth_headers(employee),
    )
    own_membership = api_client.get(
        "/api/v1/memberships/me",
        headers=auth_headers(client),
    )

    assert response.status_code == 201
    assert response.json()["remaining_visits"] == 12
    assert own_membership.status_code == 200
    assert own_membership.json()["plan_name"] == "Standard"


def test_client_cannot_issue_membership(
    api_client: ApiClient,
    user_factory: Callable[[str, UserRole], User],
    auth_headers: Callable[[User], dict[str, str]],
) -> None:
    client = user_factory("client@example.com", UserRole.CLIENT)

    response = api_client.post(
        "/api/v1/memberships",
        json={"user_id": client.id, "plan_id": 1},
        headers=auth_headers(client),
    )

    assert response.status_code == 403


def test_second_active_membership_is_rejected(
    api_client: ApiClient,
    session_factory: sessionmaker[Session],
    user_factory: Callable[[str, UserRole], User],
    auth_headers: Callable[[User], dict[str, str]],
) -> None:
    admin = user_factory("admin@example.com", UserRole.ADMIN)
    client = user_factory("client@example.com", UserRole.CLIENT)
    with session_factory() as session:
        plan = MembershipPlan(**PLAN_PAYLOAD)
        session.add(plan)
        session.commit()
        plan_id = plan.id
    payload = {"user_id": client.id, "plan_id": plan_id}

    first = api_client.post(
        "/api/v1/memberships",
        json=payload,
        headers=auth_headers(admin),
    )
    second = api_client.post(
        "/api/v1/memberships",
        json=payload,
        headers=auth_headers(admin),
    )

    assert first.status_code == 201
    assert second.status_code == 409
