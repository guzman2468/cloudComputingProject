from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.database import engine

app = FastAPI()

STATIC_DIR = Path(__file__).resolve().parent / "static"
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"
LOGIN_PAGE = TEMPLATES_DIR / "login.html"
SIGNUP_PAGE = TEMPLATES_DIR / "signup.html"

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def login_page():
    return FileResponse(LOGIN_PAGE)


@app.get("/signup")
def signup_page():
    return FileResponse(SIGNUP_PAGE)


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
