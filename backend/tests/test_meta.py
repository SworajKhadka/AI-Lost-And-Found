from fastapi.testclient import TestClient

from main import app


def test_root():
    assert TestClient(app).get("/").json()["docs"] == "/docs"


def test_cors_allows_frontend_and_blocks_others():
    client = TestClient(app)
    preflight = {"Access-Control-Request-Method": "POST"}

    ok = client.options("/items/", headers={"Origin": "https://ai-lost-and-found-five.vercel.app", **preflight})
    assert ok.headers.get("access-control-allow-origin") == "https://ai-lost-and-found-five.vercel.app"

    blocked = client.options("/items/", headers={"Origin": "https://evil.example.com", **preflight})
    assert "access-control-allow-origin" not in blocked.headers
