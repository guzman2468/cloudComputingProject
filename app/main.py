from pathlib import Path

from fastapi import Cookie, FastAPI
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.database import engine
from backend.api.routes.users import router as users_router
from backend.core.security import SESSION_COOKIE, get_session_email
from backend.core.middleware import PathTraversalMiddleware

app = FastAPI()
app.add_middleware(PathTraversalMiddleware)


@app.middleware("http")
async def protect_page_navigation(request, call_next):
    """Keep authenticated users out of auth pages and unauthenticated users out of home."""
    path = request.url.path
    authenticated = bool(get_session_email(request.cookies.get(SESSION_COOKIE)))

    if path == "/home" and not authenticated:
        return RedirectResponse(url="/", status_code=303)
    if path in {"/", "/signup"} and authenticated:
        return RedirectResponse(url="/home", status_code=303)

    response = await call_next(request)
    if path in {"/", "/signup", "/home"}:
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
        response.headers["Pragma"] = "no-cache"
    return response

STATIC_DIR = Path(__file__).resolve().parent / "static"
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
LOGIN_PAGE = TEMPLATES_DIR / "login.html"
SIGNUP_PAGE = TEMPLATES_DIR / "signup.html"
HOME_PAGE = TEMPLATES_DIR / "home.html"

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.include_router(users_router)


@app.get("/")
def login_page():
    return FileResponse(LOGIN_PAGE)


@app.get("/signup")
def signup_page():
    return FileResponse(SIGNUP_PAGE)


@app.get("/home")
def home_page(session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
    if not get_session_email(session):
        return RedirectResponse(url="/", status_code=303)
    return FileResponse(HOME_PAGE)


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "message": "MavChat is running"
    }


@app.get("/db-test")
def database_test():
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT current_database()")
        )

        return {
            "status": "connected",
            "database": result.scalar()
        }
