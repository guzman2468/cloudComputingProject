"""User account API routes."""

from fastapi import APIRouter, Cookie, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from backend.core.security import SESSION_COOKIE, SESSION_MAX_AGE, create_session_token, get_session_email
from backend.schemas.users import UserCreate, UserCreated, UserLogin, UserLoggedIn, UserProfile, UserSearchResult
from backend.services.users import (
    EmailAlreadyRegistered,
    InvalidCredentials,
    authenticate_user,
    create_user,
    get_user_profile,
    search_users,
)

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("", response_model=UserCreated, status_code=status.HTTP_200_OK)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)) -> UserCreated:
    try:
        return create_user(db, user_data)
    except EmailAlreadyRegistered as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with that email already exists. Please login or use a different email address.",
        ) from error


@router.post("/login", response_model=UserLoggedIn)
def login_user(
    login_data: UserLogin,
    response: Response,
    db: Session = Depends(get_db),
) -> UserLoggedIn:
    try:
        user = authenticate_user(db, login_data)
        response.set_cookie(
            SESSION_COOKIE,
            create_session_token(user["email"]),
            max_age=SESSION_MAX_AGE,
            httponly=True,
            samesite="lax",
            secure=False,
        )
        return user
    except InvalidCredentials as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid credentials, please try again.",
        ) from error


def require_session(session: str | None = Cookie(default=None, alias=SESSION_COOKIE)) -> str:
    email = get_session_email(session)
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return email


@router.get("/currentUser", response_model=UserProfile)
def current_user(
    email: str = Depends(require_session),
    db: Session = Depends(get_db),
) -> UserProfile:
    profile = get_user_profile(db, email)
    if not profile:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return profile


@router.get("/search", response_model=list[UserSearchResult])
def search_for_users(
    query: str = Query(min_length=1, max_length=80, alias="q"),
    email: str = Depends(require_session),
    db: Session = Depends(get_db),
) -> list[UserSearchResult]:
    return search_users(db, query, email)


@router.post("/logout")
def logout_user(response: Response) -> dict[str, str]:
    response.delete_cookie(SESSION_COOKIE)
    return {"message": "Logged out"}
