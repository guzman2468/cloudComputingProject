"""Business logic for creating users."""

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.core.security import hash_password, verify_password
from backend.schemas.users import UserCreate, UserLogin


class EmailAlreadyRegistered(Exception):
    """Raised when a user attempts to register an existing email address."""


class InvalidCredentials(Exception):
    """Raised when login credentials do not match an existing user."""


def create_user(db: Session, user_data: UserCreate) -> dict[str, int | str]:
    """Hash the password and insert a user into the existing public.users table."""
    statement = text(
        """
        INSERT INTO public.users (email, password_hash, first_name, last_name)
        VALUES (:email, :password_hash, :first_name, :last_name)
        """
    )

    try:
        row = db.execute(
            statement,
            {
                "email": user_data.email,
                "password_hash": hash_password(user_data.password),
                "first_name": user_data.first_name,
                "last_name": user_data.last_name,
            },
        )
        db.commit()
    except IntegrityError as error:
        db.rollback()
        # The table's unique constraint is the authoritative duplicate check.
        if "users_email_key" in str(error.orig) or "duplicate key" in str(error.orig).lower():
            raise EmailAlreadyRegistered from error
        raise

    return {"email": user_data.email}


def authenticate_user(db: Session, login_data: UserLogin) -> dict[str, int | str]:
    """Verify login credentials without exposing whether an email exists."""
    row = db.execute(
        text(
            """
            SELECT email, password_hash, first_name, last_name
            FROM public.users
            WHERE email = :email
            """
        ),
        {"email": login_data.email},
    ).mappings().one_or_none()

    if row is None or not verify_password(login_data.password, row["password_hash"]):
        raise InvalidCredentials

    return {
        "email": row["email"],
        "first_name": row["first_name"],
        "last_name": row["last_name"],
    }


def get_user_profile(db: Session, email: str) -> dict[str, str] | None:
    row = db.execute(
        text(
            """
            SELECT email, first_name, last_name
            FROM public.users
            WHERE email = :email
            """
        ),
        {"email": email},
    ).mappings().one_or_none()
    return dict(row) if row else None


def search_users(db: Session, query: str, current_email: str, limit: int = 20) -> list[dict[str, str]]:
    """Find other users by name or the local part of their email address."""
    normalized_query = query.strip()
    if not normalized_query:
        return []

    rows = db.execute(
        text(
            """
            SELECT email, first_name, last_name
            FROM public.users
            WHERE email <> :current_email
              AND (
                first_name ILIKE :search_pattern
                OR last_name ILIKE :search_pattern
                OR split_part(email, '@', 1) ILIKE :search_pattern
              )
            ORDER BY first_name, last_name, email
            LIMIT :result_limit
            """
        ),
        {
            "current_email": current_email,
            "search_pattern": f"%{normalized_query}%",
            "result_limit": limit,
        },
    ).mappings().all()
    return [dict(row) for row in rows]
