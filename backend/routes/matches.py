from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from pymongo.collection import Collection

from core.db import get_items_collection, parse_object_id
from core.matching import score_pair

router = APIRouter()

# Upper bound on candidates scored per request. Fine for a campus-sized
# dataset; at larger scale this would move to MongoDB Atlas Vector Search.
MAX_CANDIDATES = 500
OPPOSITE_STATUS = {"lost": "found", "found": "lost"}


class MatchRequest(BaseModel):
    item_id: str    # ID of the item to find matches for


class MatchResult(BaseModel):
    matched_item_id: str
    title: str
    description: str
    location: str
    contact: str
    match_score: int
    reasons: list[str] = []


@router.post("/", response_model=list[MatchResult])
def find_matches(request: MatchRequest, items: Collection = Depends(get_items_collection)):
    source_item = items.find_one({"_id": parse_object_id(request.item_id)}, {"owner_token": 0})
    if not source_item:
        raise HTTPException(status_code=404, detail="Item not found")

    opposite_status = OPPOSITE_STATUS.get(source_item.get("status"))
    if not opposite_status:
        raise HTTPException(status_code=400, detail="Item has an invalid status value")

    candidates = (
        items.find(
            {"status": opposite_status, "_id": {"$ne": source_item["_id"]}},
            {"owner_token": 0},
        )
        .sort("_id", -1)
        .limit(MAX_CANDIDATES)
    )

    results = []
    for candidate in candidates:
        score, reasons = score_pair(source_item, candidate)
        if score == 0:
            continue
        results.append(MatchResult(
            matched_item_id=str(candidate["_id"]),
            title=candidate["title"],
            description=candidate["description"],
            location=candidate["location"],
            contact=candidate["contact"],
            match_score=score,
            reasons=reasons,
        ))

    # Best matches first; an empty list (200 OK) simply means no match yet
    results.sort(key=lambda r: r.match_score, reverse=True)
    return results
