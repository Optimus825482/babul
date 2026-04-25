import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


class Config:
    """Flask application configuration."""

    SECRET_KEY = os.getenv("SECRET_KEY", "local-dev-secret")
    JSON_AS_ASCII = False

    # Local-first default: SQLite. Set DATABASE_URL for PostgreSQL, e.g.
    # postgresql+psycopg://postgres:postgres@localhost:5432/sercar
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'autoscout.db'}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SCRAPER_MAX_PAGES = int(os.getenv("SCRAPER_MAX_PAGES", "5"))
    SCRAPER_TIMEOUT = int(os.getenv("SCRAPER_TIMEOUT", "15"))
