import argparse
import getpass
import sys

from club_service.core.errors import ApplicationError
from club_service.domain.enums import UserRole
from club_service.infrastructure.database import get_session_factory
from club_service.services.auth import create_privileged_user


def _create_user(role: UserRole, email: str | None) -> int:
    resolved_email = email or input("Email: ").strip()
    password = getpass.getpass("Password: ")
    password_confirmation = getpass.getpass("Repeat password: ")
    if password != password_confirmation:
        print("Passwords do not match", file=sys.stderr)
        return 2
    if len(password) < 8:
        print("Password must contain at least 8 characters", file=sys.stderr)
        return 2

    with get_session_factory()() as session:
        try:
            user = create_privileged_user(session, resolved_email, password, role)
        except ApplicationError as error:
            print(error.detail, file=sys.stderr)
            return 1
    print(f"Created {user.role.value} user {user.email} with id={user.id}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="AVA Club Service administration CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    admin_parser = subparsers.add_parser("create-admin", help="Create an administrator")
    admin_parser.add_argument("--email")
    employee_parser = subparsers.add_parser("create-employee", help="Create an employee")
    employee_parser.add_argument("--email")
    arguments = parser.parse_args()

    if arguments.command == "create-admin":
        return _create_user(UserRole.ADMIN, arguments.email)
    return _create_user(UserRole.EMPLOYEE, arguments.email)


if __name__ == "__main__":
    raise SystemExit(main())
