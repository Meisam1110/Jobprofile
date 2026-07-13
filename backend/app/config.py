"""Application configuration.

Defaults run out-of-the-box on SQLite. For production point DATABASE_URL at
PostgreSQL (postgresql+psycopg2://...) — the models are dialect-neutral.
"""
from pathlib import Path

from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent
REPO_DIR = BASE_DIR.parent
DATA_DIR = REPO_DIR / "data"


class Settings(BaseSettings):
    app_name: str = "Irancell Job Profile Management System"
    database_url: str = f"sqlite:///{BASE_DIR / 'jobprofile.db'}"
    cors_origins: list[str] = ["*"]

    # AI provider — when unset, AI endpoints fall back to corpus-driven
    # heuristics (similar-profile mining) so the app works offline.
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-5"
    anthropic_base_url: str = "https://api.anthropic.com"

    # Demo auth secret (replace with SSO / Entra ID in production; see docs).
    auth_secret: str = "change-me-in-production"

    class Config:
        env_prefix = "JPMS_"
        env_file = ".env"


settings = Settings()
