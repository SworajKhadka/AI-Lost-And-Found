"""MongoDB access.

A single MongoClient is created lazily and reused for the life of the
process — MongoClient maintains its own connection pool, so creating one
per request (as the first version did) wastes connections and latency.
"""

from functools import lru_cache

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException
from pymongo import MongoClient
from pymongo.collection import Collection

from core.config import get_settings


@lru_cache
def get_client() -> MongoClient:
    settings = get_settings()
    if not settings.mongo_uri:
        raise RuntimeError("MONGO_URI is not set")
    return MongoClient(settings.mongo_uri, serverSelectionTimeoutMS=5000)


def get_items_collection() -> Collection:
    """FastAPI dependency returning the `items` collection."""
    return get_client()[get_settings().db_name]["items"]


def parse_object_id(value: str) -> ObjectId:
    """Convert a path/body id to ObjectId, answering 404 for malformed ids.

    `ObjectId("not-an-id")` raises InvalidId; left unhandled it became a
    500 response without CORS headers, which browsers report as a network
    error instead of a clean "not found".
    """
    try:
        return ObjectId(value)
    except (InvalidId, TypeError) as exc:
        raise HTTPException(status_code=404, detail="Item not found") from exc
