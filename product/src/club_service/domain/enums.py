from enum import StrEnum


class UserRole(StrEnum):
    CLIENT = "CLIENT"
    EMPLOYEE = "EMPLOYEE"
    ADMIN = "ADMIN"


class MembershipStatus(StrEnum):
    ACTIVE = "ACTIVE"
    CANCELLED = "CANCELLED"
