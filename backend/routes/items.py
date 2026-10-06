import secrets

from fastapi import APIRouter, Depends, Header, HTTPException
from pymongo.collection import Collection
from typing import Optional

from core.ai import FALLBACK_CATEGORY, extract_item_metadata
from core.db import get_items_collection, parse_object_id
from core.schemas import ItemCreate, ItemCreateResponse, ItemResponse

router = APIRouter()


# --- Helper to convert MongoDB doc to dict ---

def item_to_dict(item) -> dict:
    item["id"] = str(item["_id"])
    del item["_id"]
    return item


# --- Routes ---

@router.get("/", response_model=list[ItemResponse])
def get_all_items(items: Collection = Depends(get_items_collection)):
    docs = list(items.find().sort("_id", 1))
    return [item_to_dict(doc) for doc in docs]


@router.get("/{item_id}", response_model=ItemResponse)
def get_item(item_id: str, items: Collection = Depends(get_items_collection)):
    oid = parse_object_id(item_id)
    item = items.find_one({"_id": oid})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item_to_dict(item)


@router.post("/", response_model=ItemCreateResponse, status_code=201)
def create_item(item: ItemCreate, items: Collection = Depends(get_items_collection)):

    # Generate a secure random token — the creator receives this once in the
    # response so their browser can authenticate future delete requests.
    owner_token = secrets.token_hex(16)

    metadata = extract_item_metadata(item.title, item.description)

    doc = {
        **item.model_dump(),
        "category":    metadata["category"] if metadata else FALLBACK_CATEGORY,
        "keywords":    metadata["keywords"] if metadata else [],
        # Lets scripts/retag_items.py find items whose AI tagging failed
        "ai_status":   "ok" if metadata else "pending",
        "owner_token": owner_token,   # stored in DB, never exposed in GET responses
    }

    result  = items.insert_one(doc)
    created = items.find_one({"_id": result.inserted_id})
    return item_to_dict(created)


@router.delete("/{item_id}")
def delete_item(
    item_id: str,
    # FastAPI maps the X-Owner-Token HTTP header to this parameter automatically
    x_owner_token: Optional[str] = Header(None),
    items: Collection = Depends(get_items_collection),
):
    oid = parse_object_id(item_id)
    item = items.find_one({"_id": oid})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Reject the request if no token was supplied or if it doesn't match
    if not x_owner_token or x_owner_token != item.get("owner_token"):
        raise HTTPException(
            status_code=403,
            detail="Forbidden: invalid or missing owner token.",
        )

    items.delete_one({"_id": oid})
    return {"message": "Item deleted successfully"}
