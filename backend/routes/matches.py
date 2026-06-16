import os

from bson import ObjectId
from fastapi import APIRouter, HTTPException
from pymongo import MongoClient
from pydantic import BaseModel

router = APIRouter()


# --- Database connection ---

def get_db():
    client = MongoClient(os.getenv("MONGO_URI"))
    return client["lost_and_found"]


# --- Request / Response models ---

class MatchRequest(BaseModel):
    item_id: str    # ID of the newly created item to find matches for


class MatchResult(BaseModel):
    matched_item_id: str
    title: str
    description: str
    location: str
    contact: str
    match_score: int


# --- Scoring logic ---

def calculate_score(source_item: dict, candidate: dict) -> int:
    """
    Scores how likely two items are the same object (0-100).

    Scoring breakdown:
      +40  if category matches exactly
      +15  per overlapping keyword (up to 4 overlaps = +60 max)
    """
    score = 0

    # Category match: both items were classified as the same type of object
    if source_item.get("category") and source_item["category"] == candidate.get("category"):
        score += 40

    # Keyword overlap: compare the Gemini-extracted keyword lists
    source_keywords = set(kw.lower() for kw in source_item.get("keywords", []))
    candidate_keywords = set(kw.lower() for kw in candidate.get("keywords", []))
    overlap_count = len(source_keywords & candidate_keywords)
    score += min(overlap_count * 15, 60)   # cap keyword contribution at 60

    return min(score, 100)


# --- Routes ---

@router.post("/", response_model=list[MatchResult])
def find_matches(request: MatchRequest):
    db = get_db()

    # Fetch the source item by ID
    try:
        source_item = db["items"].find_one({"_id": ObjectId(request.item_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid item_id format")

    if not source_item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Determine which status to search for — opposite of the source item
    source_status = source_item.get("status")
    if source_status == "lost":
        opposite_status = "found"
    elif source_status == "found":
        opposite_status = "lost"
    else:
        raise HTTPException(status_code=400, detail="Item has an invalid status value")

    source_category = source_item.get("category")
    source_keywords = [kw.lower() for kw in source_item.get("keywords", [])]

    # Query MongoDB for candidates that share the category OR have keyword overlap.
    # We fetch a broad set here and do precise scoring in Python below.
    candidates = list(db["items"].find({
        "status": opposite_status,
        "_id": {"$ne": source_item["_id"]},     # exclude the source item itself
        "$or": [
            {"category": source_category},      # exact category match
            {"keywords": {"$in": source_keywords}},  # at least one keyword in common
        ],
    }))

    # Score each candidate and keep only those with 2+ keyword overlaps
    # OR a category match (i.e. a meaningful signal, not a single-keyword fluke)
    results = []
    for candidate in candidates:
        score = calculate_score(source_item, candidate)

        # Require at least a category match (+40) or 2 keyword overlaps (+30) to surface
        if score < 30:
            continue

        results.append(MatchResult(
            matched_item_id=str(candidate["_id"]),
            title=candidate["title"],
            description=candidate["description"],
            location=candidate["location"],
            contact=candidate["contact"],
            match_score=score,
        ))

    # Sort best matches first
    results.sort(key=lambda r: r.match_score, reverse=True)

    # Return empty list (200 OK) when nothing qualifies — not an error
    return results
