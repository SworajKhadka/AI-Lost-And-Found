import json
import os
import re
import secrets

import google.generativeai as genai
from bson import ObjectId
from fastapi import APIRouter, Header, HTTPException
from pymongo import MongoClient
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


# --- Database connection ---

def get_db():
    client = MongoClient(os.getenv("MONGO_URI"))
    return client["lost_and_found"]


# --- Request / Response models ---

class Item(BaseModel):
    title: str
    description: str
    # "lost" or "found" — whether the person lost or found this object
    status: str
    location: str
    contact: str
    image_url: Optional[str] = None


class ItemResponse(Item):
    id: str
    category: str
    keywords: list[str]
    # owner_token is intentionally absent — callers never see other items' tokens


class ItemCreateResponse(ItemResponse):
    # Extends ItemResponse to include the token, but ONLY on the POST response.
    # The creator receives it once so the frontend can store it for later deletes.
    owner_token: str


# --- Gemini metadata extraction ---

def extract_item_metadata(description: str) -> dict:
    """
    Calls Gemini to classify the item and extract keywords from the description.
    Returns {"category": str, "keywords": [str, ...]}.
    Falls back to safe defaults if anything goes wrong.
    """
    fallback = {"category": "uncategorized", "keywords": []}

    try:
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel("gemini-2.5-flash")

        prompt = (
            "You are a classifier for a lost-and-found app.\n\n"
            f'Item description: "{description}"\n\n'
            "Return a JSON object with exactly two keys:\n"
            '  "category": one of [earbuds, wallet, ID card, charger, keys, bag, phone, laptop, other]\n'
            '  "keywords": a list of 3 to 5 short keywords that best describe the item\n\n'
            "Reply with ONLY the JSON object, no extra text."
        )

        response = model.generate_content(prompt)
        raw = response.text.strip()

        # Strip markdown code fences if Gemini wraps the JSON in ```json ... ```
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        parsed = json.loads(raw)

        category = str(parsed.get("category", "uncategorized"))
        keywords = parsed.get("keywords", [])
        if not isinstance(keywords, list):
            keywords = []

        return {"category": category, "keywords": keywords}

    except Exception as e:
        print(f"Gemini error: {e}")
        return fallback


# --- Helper to convert MongoDB doc to dict ---

def item_to_dict(item) -> dict:
    item["id"] = str(item["_id"])
    del item["_id"]
    return item


# --- Routes ---

@router.get("/", response_model=list[ItemResponse])
def get_all_items():
    db = get_db()
    items = list(db["items"].find())
    return [item_to_dict(item) for item in items]


@router.get("/{item_id}", response_model=ItemResponse)
def get_item(item_id: str):
    db = get_db()
    item = db["items"].find_one({"_id": ObjectId(item_id)})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item_to_dict(item)


@router.post("/", response_model=ItemCreateResponse, status_code=201)
def create_item(item: Item):
    db = get_db()

    # Generate a secure random token — the creator receives this once in the
    # response so their browser can authenticate future delete requests.
    owner_token = secrets.token_hex(16)

    metadata = extract_item_metadata(item.description)

    doc = {
        **item.model_dump(),
        "category":    metadata["category"],
        "keywords":    metadata["keywords"],
        "owner_token": owner_token,   # stored in DB, never exposed in GET responses
    }

    result  = db["items"].insert_one(doc)
    created = db["items"].find_one({"_id": result.inserted_id})
    return item_to_dict(created)


@router.delete("/{item_id}")
def delete_item(
    item_id: str,
    # FastAPI maps the X-Owner-Token HTTP header to this parameter automatically
    x_owner_token: Optional[str] = Header(None),
):
    db = get_db()

    item = db["items"].find_one({"_id": ObjectId(item_id)})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Reject the request if no token was supplied or if it doesn't match
    if not x_owner_token or x_owner_token != item.get("owner_token"):
        raise HTTPException(
            status_code=403,
            detail="Forbidden: invalid or missing owner token.",
        )

    db["items"].delete_one({"_id": ObjectId(item_id)})
    return {"message": "Item deleted successfully"}
