def test_lost_item_matches_found_item_of_same_object(client, make_item):
    lost = make_item(status="lost")
    found = make_item(title="Found a MacBook", description="Laptop left in the library", status="found")
    make_item(title="Black iPhone", description="Phone with a cracked screen", status="found")

    response = client.post("/matches/", json={"item_id": lost["id"]})
    assert response.status_code == 200
    matches = response.json()
    assert [m["matched_item_id"] for m in matches] == [found["id"]]
    assert matches[0]["match_score"] >= 80
    assert any("Same category" in reason for reason in matches[0]["reasons"])


def test_items_with_same_status_never_match(client, make_item):
    lost = make_item(status="lost")
    make_item(title="Another lost MacBook", status="lost")
    assert client.post("/matches/", json={"item_id": lost["id"]}).json() == []


def test_matches_are_sorted_best_first(client, collection, make_item):
    lost = make_item(status="lost")
    strong = make_item(title="Found MacBook", status="found")
    weak = make_item(title="Found a laptop sleeve", description="Grey laptop sleeve", status="found")
    # Make the second candidate only partially similar
    collection.update_one({"title": weak["title"]}, {"$set": {"embedding": [0.8, 0.6, 0.0], "keywords": ["sleeve"]}})

    ids = [m["matched_item_id"] for m in client.post("/matches/", json={"item_id": lost["id"]}).json()]
    assert ids[0] == strong["id"]


def test_match_request_for_unknown_or_malformed_id_returns_404(client):
    assert client.post("/matches/", json={"item_id": "nope"}).status_code == 404
    assert client.post("/matches/", json={"item_id": "0123456789abcdef01234567"}).status_code == 404
