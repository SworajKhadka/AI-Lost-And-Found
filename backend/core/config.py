"""Central place for environment-driven settings."""

import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()

# Production frontend plus local Vite dev server. Vercel preview deployments
# for this project are matched by FRONTEND_ORIGIN_REGEX below.
DEFAULT_ALLOWED_ORIGINS = [
    "https://ai-lost-and-found-five.vercel.app",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
FRONTEND_ORIGIN_REGEX = r"https://ai-lost-and-found(-[a-z0-9-]+)?\.vercel\.app"


class Settings:
    def __init__(self) -> None:
        self.mongo_uri: str | None = os.getenv("MONGO_URI")
        self.db_name: str = os.getenv("MONGO_DB_NAME", "lost_and_found")
        self.gemini_api_key: str | None = os.getenv("GEMINI_API_KEY")
        self.gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.embedding_model: str = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")

        extra = os.getenv("ALLOWED_ORIGINS", "")
        self.allowed_origins: list[str] = DEFAULT_ALLOWED_ORIGINS + [
            o.strip().rstrip("/") for o in extra.split(",") if o.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
