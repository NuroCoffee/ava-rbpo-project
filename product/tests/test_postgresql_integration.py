import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from club_service.core.security import hash_password
from club_service.domain.enums import MembershipStatus, UserRole
from club_service.infrastructure.models import Base, Membership, MembershipPlan, User, Visit
from club_service.services.visits import register_visit


@pytest.mark.postgresql
def test_postgresql_visit_idempotency_and_unique_constraint() -> None:
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("TEST_DATABASE_URL is not configured")

    schema = f"club_test_{uuid4().hex}"
    admin_engine = create_engine(database_url)
    with admin_engine.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    engine = create_engine(
        database_url,
        connect_args={"options": f"-csearch_path={schema}"},
    )
    try:
        Base.metadata.create_all(engine)
        factory = sessionmaker(bind=engine, expire_on_commit=False)
        _assert_postgresql_idempotency(factory)
    finally:
        engine.dispose()
        with admin_engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin_engine.dispose()


def _assert_postgresql_idempotency(factory: sessionmaker[Session]) -> None:
    now = datetime.now(UTC)
    with factory() as session:
        employee = User(
            email="employee-integration@example.com",
            password_hash=hash_password("secure-password"),
            role=UserRole.EMPLOYEE,
        )
        client = User(
            email="client-integration@example.com",
            password_hash=hash_password("secure-password"),
            role=UserRole.CLIENT,
        )
        plan = MembershipPlan(
            name="Integration plan",
            duration_days=30,
            visits_limit=2,
            freeze_days_limit=0,
        )
        membership = Membership(
            user=client,
            plan=plan,
            starts_at=now,
            expires_at=now + timedelta(days=30),
            remaining_visits=2,
            status=MembershipStatus.ACTIVE,
        )
        session.add_all([employee, membership])
        session.commit()
        key = uuid4()

        first = register_visit(session, client.id, employee.id, key)
        second = register_visit(session, client.id, employee.id, key)

        assert first.id == second.id
        assert session.scalar(select(func.count()).select_from(Visit)) == 1
        session.refresh(membership)
        assert membership.remaining_visits == 1

        duplicate = Visit(
            membership_id=membership.id,
            registered_by=employee.id,
            visited_at=now,
            idempotency_key=key,
        )
        session.add(duplicate)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
        assert session.scalar(select(func.count()).select_from(Visit)) == 1
