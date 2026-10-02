from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from club_service.domain.enums import MembershipStatus, UserRole

metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
)


class Base(DeclarativeBase):
    metadata = metadata


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False, length=16),
        default=UserRole.CLIENT,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    memberships: Mapped[list["Membership"]] = relationship(back_populates="user")
    registered_visits: Mapped[list["Visit"]] = relationship(
        back_populates="registrar",
        foreign_keys="Visit.registered_by",
    )


class MembershipPlan(Base):
    __tablename__ = "membership_plans"
    __table_args__ = (
        CheckConstraint("duration_days > 0", name="duration_days_positive"),
        CheckConstraint(
            "visits_limit IS NULL OR visits_limit > 0",
            name="visits_limit_positive",
        ),
        CheckConstraint("freeze_days_limit >= 0", name="freeze_days_limit_nonnegative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    duration_days: Mapped[int] = mapped_column(Integer)
    visits_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    freeze_days_limit: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    memberships: Mapped[list["Membership"]] = relationship(back_populates="plan")


class Membership(Base):
    __tablename__ = "memberships"
    __table_args__ = (
        CheckConstraint("expires_at > starts_at", name="valid_date_range"),
        CheckConstraint(
            "remaining_visits IS NULL OR remaining_visits >= 0",
            name="remaining_visits_nonnegative",
        ),
        Index("ix_memberships_user_status_expires", "user_id", "status", "expires_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    plan_id: Mapped[int] = mapped_column(
        ForeignKey("membership_plans.id", ondelete="RESTRICT")
    )
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    remaining_visits: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[MembershipStatus] = mapped_column(
        Enum(MembershipStatus, native_enum=False, length=16),
        default=MembershipStatus.ACTIVE,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    user: Mapped[User] = relationship(back_populates="memberships")
    plan: Mapped[MembershipPlan] = relationship(back_populates="memberships")
    visits: Mapped[list["Visit"]] = relationship(back_populates="membership")


class Visit(Base):
    __tablename__ = "visits"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_visits_idempotency_key"),
        Index("ix_visits_membership_visited_at", "membership_id", "visited_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    membership_id: Mapped[int] = mapped_column(
        ForeignKey("memberships.id", ondelete="RESTRICT")
    )
    registered_by: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    visited_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    idempotency_key: Mapped[UUID] = mapped_column(unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    membership: Mapped[Membership] = relationship(back_populates="visits")
    registrar: Mapped[User] = relationship(
        back_populates="registered_visits",
        foreign_keys=[registered_by],
    )
