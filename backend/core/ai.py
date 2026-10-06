"""Gemini integration (google-genai SDK).

The original code used `google-generativeai`, which Google has deprecated
and no longer maintains. This module uses the supported `google-genai`
client with:
  * structured JSON output constrained to a schema (no regex-stripping of
    markdown fences, no free-form category strings),
  * automatic retries with exponential backoff for 429 / 5xx responses,
    which were the main reason items were silently saved as
    "uncategorized" with no keywords.
"""

import logging
from enum import Enum
from functools import lru_cache

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from core.config import get_settings

logger = logging.getLogger(__name__)


class Category(str, Enum):
    earbuds = "earbuds"
    headphones = "headphones"
    phone = "phone"
    laptop = "laptop"
    tablet = "tablet"
    charger = "charger"
    watch = "watch"
    wallet = "wallet"
    id_card = "ID card"
    keys = "keys"
    bag = "bag"
    bottle = "bottle"
    umbrella = "umbrella"
    clothing = "clothing"
    jewelry = "jewelry"
    book = "book"
    stationery = "stationery"
    other = "other"


class ItemMetadata(BaseModel):
    category: Category
    keywords: list[str] = Field(description="3 to 5 short lowercase keywords")


FALLBACK_CATEGORY = "uncategorized"

CLASSIFY_PROMPT = """You classify items for a campus lost-and-found app.

Title: {title}
Description: {description}

Pick the single best category and 3-5 short lowercase keywords that would
help match this item with a report of the same object (brand, colour,
type, distinguishing features). Do not include locations or people."""


@lru_cache
def get_client() -> genai.Client:
    settings = get_settings()
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")
    return genai.Client(
        api_key=settings.gemini_api_key,
        http_options=types.HttpOptions(
            timeout=20_000,  # ms
            retry_options=types.HttpRetryOptions(attempts=4, initial_delay=1.0, max_delay=8.0),
        ),
    )


def _clean_keywords(raw: list[str]) -> list[str]:
    seen: list[str] = []
    for kw in raw:
        kw = str(kw).strip().lower()
        if kw and kw not in seen:
            seen.append(kw)
    return seen[:5]


def extract_item_metadata(title: str, description: str) -> dict | None:
    """Classify an item and extract keywords.

    Returns {"category": str, "keywords": [str]} or None if Gemini could
    not be reached after retries — callers store a fallback and flag the
    item so scripts/retag_items.py can repair it later.
    """
    try:
        response = get_client().models.generate_content(
            model=get_settings().gemini_model,
            contents=CLASSIFY_PROMPT.format(title=title, description=description),
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ItemMetadata,
                temperature=0.2,
            ),
        )
        parsed = response.parsed
        if not isinstance(parsed, ItemMetadata):
            parsed = ItemMetadata.model_validate_json(response.text)
        return {"category": parsed.category.value, "keywords": _clean_keywords(parsed.keywords)}
    except Exception:
        logger.exception("Gemini classification failed")
        return None


EMBEDDING_DIMENSIONS = 768


def item_embedding_text(item: dict) -> str:
    """The text that represents an item in vector space."""
    parts = [item.get("title", ""), item.get("description", "")]
    category = item.get("category")
    if category and category != FALLBACK_CATEGORY:
        parts.append(f"Category: {category}")
    if item.get("keywords"):
        parts.append("Keywords: " + ", ".join(item["keywords"]))
    return ". ".join(p.strip() for p in parts if p and p.strip())


def embed_text(text: str) -> list[float] | None:
    """Return a semantic embedding for `text`, or None if Gemini fails.

    Embeddings let matching understand that "AirPods" and "white earbuds"
    describe the same thing even when no keyword is shared.
    """
    try:
        result = get_client().models.embed_content(
            model=get_settings().embedding_model,
            contents=text,
            config=types.EmbedContentConfig(
                task_type="SEMANTIC_SIMILARITY",
                output_dimensionality=EMBEDDING_DIMENSIONS,
            ),
        )
        values = result.embeddings[0].values if result.embeddings else None
        return list(values) if values else None
    except Exception:
        logger.exception("Gemini embedding failed")
        return None
