import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import FRONTEND_ORIGIN_REGEX, get_settings
from core.db import get_client
from routes.items import router as items_router
from routes.matches import router as matches_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

settings = get_settings()

app = FastAPI(
    title="AI Lost and Found API",
    description="Report lost or found items; Gemini tags them and suggests likely matches.",
    version="1.1.0",
)

# Only the deployed frontend (plus its Vercel previews) and local dev may
# call the API from a browser. Extra origins can be added with ALLOWED_ORIGINS.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_origin_regex=FRONTEND_ORIGIN_REGEX,
    allow_credentials=False,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "X-Owner-Token"],
)

app.include_router(items_router, prefix="/items", tags=["items"])
app.include_router(matches_router, prefix="/matches", tags=["matches"])


@app.get("/", tags=["meta"])
def root():
    return {"message": "AI Lost and Found API is running", "docs": "/docs"}


@app.get("/health", tags=["meta"])
def health():
    """Liveness + database connectivity check for uptime monitors."""
    try:
        get_client().admin.command("ping")
        database = "ok"
    except Exception:
        database = "unreachable"
    return {"status": "ok" if database == "ok" else "degraded", "database": database}
