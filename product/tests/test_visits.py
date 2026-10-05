from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from club_service.domain.enums import MembershipStatus, UserRole
from club_service.infrastructure.models import Membership, MembershipPlan, User, Visit
from tests.conftest import ApiClient


def _create_membership(
    session_factory: sessionmaker[Session],
    client: User,
    *,
    visits_limit: int | None = 3,
    status: MembershipStatus = MembershipStatus.ACTIVE,
    starts_at: datetime | None = None,
    expires_at: datetime | None = None,
) -> int:
    now = datetime.now(UTC)
    with session_factory() as session:
        plan = MembershipPlan(
            name=f"Plan-{uuid4()}",
            duration_days=30,
            visits_limit=visits_limit,
            freeze_days_limit=0,
        )
        membership = Membership(
            user_id=client.id,
            plan=plan,
            starts_at=starts_at or now,
            expires_at=expires_at or now + timedelta(days=30),
            remaining_visits=visits_limit,
            status=status,
        )
        session.add(membership)
        session.commit()
        return membership.id


def test_visit_decrements_remaining_visits_once_and_is_idempotent(
    api_client: ApiClient,
    session_factory: sessionmaker[Session],
    user_factory: Callable[[str, UserRole], User],
    auth_headers: Callable[[User], dict[str, str]],
) -> None:
    employee = user_factory("employee@example.com", UserRole.EMPLOYEE)
    client = user_factory("client@example.com", UserRole.CLIENT)
    membership_id = _create_membership(session_factory, client)
    key = str(uuid4())
    payload = {"user_id": client.id, "idempotency_key": key}

    first = api_client.post("/api/v1/visits", json=payload, headers=auth_headers(employee))
    second = api_client.post("/api/v1/visits", json=payload, headers=auth_headers(employee))

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    with session_factory() as session:
        membership = session.get(Membership, membership_id)
        visit_count = session.scalar(select(func.count()).select_from(Visit))
        assert membership is not None
        assert membership.remaining_visits == 2
        assert visit_count == 1


def test_unlimited_membership_keeps_null_remaining_visits(
    api_client: ApiClient,
    session_factory: sessionmaker[Session],
    user_factory: Callable[[str, UserRole], User],
    auth_headers: Callable[[User], dict[str, str]],
) -> None:
    admin = user_factory("admin@example.com", UserRole.ADMIN)
    client = user_factory("client@example.com", UserRole.CLIENT)
    membership_id = _create_membership(session_factory, client, visits_limit=None)

    response = api_client.post(
        "/api/v1/visits",
        json={"user_id": client.id, "idempotency_key": str(uuid4())},
        headers=auth_headers(admin),
    )

    assert response.status_code == 201
    with session_factory() as session:
        membership = session.get(Membership, membership_id)
        assert membership is not None
        assert membership.remaining_visits is None


@pytest.mark.parametrize(
    ("status", "remaining_visits", "expired"),
    [
        (MembershipStatus.CANCELLED, 3, False),
        (MembershipStatus.ACTIVE, 3, True),
        (MembershipStatus.ACTIVE, 0, False),
    ],
)
def test_invalid_membership_rejects_visit(
    api_client: ApiClient,
    session_factory: sessionmaker[Session],
    user_factory: Callable[[str, UserRole], User],
    auth_headers: Callable[[User], dict[str, str]],
    status: MembershipStatus,
    remaining_visits: int,
    expired: bool,
) -> None:
    employee = user_factory("employee@example.com", UserRole.EMPLOYEE)
    client = user_factory("client@example.com", UserRole.CLIENT)
    now = datetime.now(UTC)
    membership_id = _create_membership(
        session_factory,
        client,
        visits_limit=max(remaining_visits, 1),
        status=status,
        starts_at=now - timedelta(days=30) if expired else now,
        expires_at=now - timedelta(days=1) if expired else now + timedelta(days=30),
    )
    if remaining_visits == 0:
        with session_factory() as session:
            membership = session.get(Membership, membership_id)
            assert membership is not None
            membership.remaining_visits = 0
            session.commit()

    response = api_client.post(
        "/api/v1/visits",
        json={"user_id": client.id, "idempotency_key": str(uuid4())},
        headers=auth_headers(employee),
    )

    assert response.status_code == 409


def test_client_cannot_register_visit(
    api_client: ApiClient,
    user_factory: Callable[[str, UserRole], User],
    auth_headers: Callable[[User], dict[str, str]],
) -> None:
    client = user_factory("client@example.com", UserRole.CLIENT)

    response = api_client.post(
        "/api/v1/visits",
        json={"user_id": client.id, "idempotency_key": str(uuid4())},
        headers=auth_headers(client),
    )

    assert response.status_code == 403


def test_visit_history_contains_only_current_clients_visits(
    api_client: ApiClient,
    session_factory: sessionmaker[Session],
    user_factory: Callable[[str, UserRole], User],
    auth_headers: Callable[[User], dict[str, str]],
) -> None:
    employee = user_factory("employee@example.com", UserRole.EMPLOYEE)
    client_a = user_factory("a@example.com", UserRole.CLIENT)
    client_b = user_factory("b@example.com", UserRole.CLIENT)
    _create_membership(session_factory, client_a)
    _create_membership(session_factory, client_b)
    for client in (client_a, client_b):
        response = api_client.post(
            "/api/v1/visits",
            json={"user_id": client.id, "idempotency_key": str(uuid4())},
            headers=auth_headers(employee),
        )
        assert response.status_code == 201

    response = api_client.get("/api/v1/visits/me", headers=auth_headers(client_a))

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["membership_id"] != 0
