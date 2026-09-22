from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.database import engine

app = FastAPI()

STATIC_DIR = Path(__file__).resolve().parent / "static"
HOME_PAGE = STATIC_DIR / "pages" / "home.html"

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def home_page():
    return FileResponse(HOME_PAGE)


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "message": "Nebraska Chat is running"
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
