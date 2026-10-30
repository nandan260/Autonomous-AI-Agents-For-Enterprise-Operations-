import os
from pathlib import Path
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

BACKEND_DIR = Path(__file__).resolve().parent
UPLOADS_DIR = BACKEND_DIR / "uploads" / "test_docs"
FRONTEND_DIST_DIR = ROOT_DIR / "frontend" / "dist"

UPLOADS_DIR.mkdir(parents=True, exist_ok=True)


def get_database_url() -> str:
    """Build the database URL, defaulting to local SQLite if Postgres is not configured."""
    explicit_url = os.getenv("DATABASE_URL")
    if explicit_url:
        return explicit_url

    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    database = os.getenv("POSTGRES_DB")

    if user and password and database and user != "change_me" and password != "change_me":
        return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"

    # Default to clean, reliable SQLite for local zero-config execution
    db_file = BACKEND_DIR / "onboarding.db"
    return f"sqlite:///{db_file.as_posix()}"


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
