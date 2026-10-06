import routes.items as items_routes


def test_create_item_returns_ai_tags_and_owner_token(make_item):
    item = make_item()
    assert item["category"] == "laptop"
    assert "macbook" in item["keywords"]
    assert len(item["owner_token"]) == 32
    assert "embedding" not in item


def test_list_items_never_exposes_private_fields(client, make_item):
    make_item()
    response = client.get("/items/")
    assert response.status_code == 200
    [item] = response.json()
    assert "owner_token" not in item
    assert "embedding" not in item


def test_list_items_is_oldest_first(client, make_item):
    first = make_item(title="First item")
    second = make_item(title="Second item")
    ids = [item["id"] for item in client.get("/items/").json()]
    assert ids == [first["id"], second["id"]]


def test_get_item_by_id(client, make_item):
    created = make_item()
    response = client.get(f"/items/{created['id']}")
    assert response.status_code == 200
    assert response.json()["title"] == created["title"]


def test_malformed_id_returns_404_not_500(client):
    assert client.get("/items/not-an-id").status_code == 404
    assert client.delete("/items/not-an-id", headers={"X-Owner-Token": "x"}).status_code == 404


def test_unknown_id_returns_404(client):
    assert client.get("/items/0123456789abcdef01234567").status_code == 404


def test_invalid_status_is_rejected(client):
    response = client.post(
        "/items/",
        json={"title": "Keys", "description": "Car keys on a ring", "status": "stolen",
              "location": "Gym", "contact": "a@b.com"},
    )
    assert response.status_code == 422


def test_blank_fields_are_rejected_after_trimming(client):
    response = client.post(
        "/items/",
        json={"title": "   ", "description": "Car keys on a ring", "status": "lost",
              "location": "Gym", "contact": "a@b.com"},
    )
    assert response.status_code == 422


def test_gemini_failure_falls_back_and_flags_item(client, collection, monkeypatch):
    monkeypatch.setattr(items_routes, "extract_item_metadata", lambda *_: None)
    response = client.post(
        "/items/",
        json={"title": "Water bottle", "description": "Blue steel bottle", "status": "found",
              "location": "Canteen", "contact": "a@b.com"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["category"] == "uncategorized"
    assert body["keywords"] == []
    assert collection.find_one({"title": "Water bottle"})["ai_status"] == "pending"


def test_delete_requires_matching_owner_token(client, make_item):
    item = make_item()
    url = f"/items/{item['id']}"

    assert client.delete(url).status_code == 403
    assert client.delete(url, headers={"X-Owner-Token": "wrong"}).status_code == 403
    assert client.delete(url, headers={"X-Owner-Token": item["owner_token"]}).status_code == 200
    assert client.get(url).status_code == 404
