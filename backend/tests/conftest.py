"""Test fixtures: an in-memory MongoDB and a fake Gemini.

No network calls are made — the API is exercised end-to-end through
FastAPI's TestClient with mongomock standing in for MongoDB and
deterministic stand-ins for the Gemini tagging/embedding functions.
"""

import os

import mongomock
import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("MONGO_URI", "mongodb://test")
os.environ.setdefault("GEMINI_API_KEY", "test-key")

import routes.items as items_routes  # noqa: E402
from core.db import get_items_collection  # noqa: E402
from main import app  # noqa: E402

# Tiny hand-made "embedding space": items about the same object share a direction.
FAKE_VECTORS = {
    "laptop": [1.0, 0.0, 0.0],
    "phone": [0.0, 1.0, 0.0],
    "earbuds": [0.0, 0.0, 1.0],
}


def fake_metadata(title: str, description: str) -> dict:
    text = f"{title} {description}".lower()
    if "macbook" in text or "laptop" in text:
        return {"category": "laptop", "keywords": ["macbook", "laptop", "silver"]}
    if "iphone" in text or "phone" in text:
        return {"category": "phone", "keywords": ["iphone", "black"]}
    if "airpods" in text or "earbuds" in text:
        return {"category": "earbuds", "keywords": ["white", "case"]}
    return {"category": "other", "keywords": ["misc"]}


def fake_embed(text: str) -> list[float]:
    text = text.lower()
    for key, vector in FAKE_VECTORS.items():
        if key in text:
            return vector
    return [0.577, 0.577, 0.577]


@pytest.fixture
def collection():
    return mongomock.MongoClient()["lost_and_found_test"]["items"]


@pytest.fixture
def client(collection, monkeypatch):
    monkeypatch.setattr(items_routes, "extract_item_metadata", fake_metadata)
    monkeypatch.setattr(items_routes, "embed_text", fake_embed)
    app.dependency_overrides[get_items_collection] = lambda: collection
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def make_item(client):
    def _make(**overrides):
        payload = {
            "title": "Silver MacBook Air",
            "description": "13 inch MacBook with stickers on the lid",
            "status": "lost",
            "location": "Library 2nd floor",
            "contact": "student@example.com",
        }
        payload.update(overrides)
        response = client.post("/items/", json=payload)
        assert response.status_code == 201, response.text
        return response.json()

    return _make
