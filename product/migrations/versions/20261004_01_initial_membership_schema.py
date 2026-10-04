"""Create users, membership plans, memberships, and visits.

Revision ID: 20261004_01
Revises:
Create Date: 2026-10-04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261004_01"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "role",
            sa.Enum(
                "CLIENT",
                "EMPLOYEE",
                "ADMIN",
                name="user_role",
                native_enum=False,
                length=16,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=False)
    op.create_index(op.f("ix_users_role"), "users", ["role"], unique=False)

    op.create_table(
        "membership_plans",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("duration_days", sa.Integer(), nullable=False),
        sa.Column("visits_limit", sa.Integer(), nullable=True),
        sa.Column("freeze_days_limit", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "duration_days > 0",
            name=op.f("ck_membership_plans_duration_days_positive"),
        ),
        sa.CheckConstraint(
            "visits_limit IS NULL OR visits_limit > 0",
            name=op.f("ck_membership_plans_visits_limit_positive"),
        ),
        sa.CheckConstraint(
            "freeze_days_limit >= 0",
            name=op.f("ck_membership_plans_freeze_days_limit_nonnegative"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_membership_plans")),
        sa.UniqueConstraint("name", name=op.f("uq_membership_plans_name")),
    )

    op.create_table(
        "memberships",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("plan_id", sa.Integer(), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("remaining_visits", sa.Integer(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "ACTIVE",
                "CANCELLED",
                name="membership_status",
                native_enum=False,
                length=16,
                create_constraint=True,
            ),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("expires_at > starts_at", name=op.f("ck_memberships_valid_date_range")),
        sa.CheckConstraint(
            "remaining_visits IS NULL OR remaining_visits >= 0",
            name=op.f("ck_memberships_remaining_visits_nonnegative"),
        ),
        sa.ForeignKeyConstraint(
            ["plan_id"],
            ["membership_plans.id"],
            name=op.f("fk_memberships_plan_id_membership_plans"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_memberships_user_id_users"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_memberships")),
    )
    op.create_index(op.f("ix_memberships_expires_at"), "memberships", ["expires_at"])
    op.create_index(op.f("ix_memberships_status"), "memberships", ["status"])
    op.create_index(
        "ix_memberships_user_status_expires",
        "memberships",
        ["user_id", "status", "expires_at"],
    )

    op.create_table(
        "visits",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("membership_id", sa.Integer(), nullable=False),
        sa.Column("registered_by", sa.Integer(), nullable=False),
        sa.Column("visited_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("idempotency_key", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["membership_id"],
            ["memberships.id"],
            name=op.f("fk_visits_membership_id_memberships"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["registered_by"],
            ["users.id"],
            name=op.f("fk_visits_registered_by_users"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_visits")),
        sa.UniqueConstraint("idempotency_key", name="uq_visits_idempotency_key"),
    )
    op.create_index(
        "ix_visits_membership_visited_at",
        "visits",
        ["membership_id", "visited_at"],
    )
    op.create_index(op.f("ix_visits_visited_at"), "visits", ["visited_at"])


def downgrade() -> None:
    op.drop_index(op.f("ix_visits_visited_at"), table_name="visits")
    op.drop_index("ix_visits_membership_visited_at", table_name="visits")
    op.drop_table("visits")
    op.drop_index("ix_memberships_user_status_expires", table_name="memberships")
    op.drop_index(op.f("ix_memberships_status"), table_name="memberships")
    op.drop_index(op.f("ix_memberships_expires_at"), table_name="memberships")
    op.drop_table("memberships")
    op.drop_table("membership_plans")
    op.drop_index(op.f("ix_users_role"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
