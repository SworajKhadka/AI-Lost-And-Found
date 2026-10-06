"""Request / response models shared by the API routes."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ItemStatus = Literal["lost", "found"]


class ItemCreate(BaseModel):
    """Payload accepted when reporting a lost or found item."""

    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=2, max_length=100)
    description: str = Field(min_length=5, max_length=1000)
    # Whether the reporter lost or found this object
    status: ItemStatus
    location: str = Field(min_length=2, max_length=120)
    contact: str = Field(min_length=3, max_length=120)
    image_url: str | None = Field(default=None, max_length=500)


class ItemResponse(BaseModel):
    """Public view of an item. Never includes owner_token or embeddings."""

    id: str
    title: str
    description: str
    # str (not ItemStatus) so legacy documents can still be serialised
    status: str
    location: str
    contact: str
    image_url: str | None = None
    category: str = "uncategorized"
    keywords: list[str] = []
    created_at: datetime | None = None


class ItemCreateResponse(ItemResponse):
    # Returned ONLY from POST so the creator's browser can store it and
    # authorise a later delete. It is never exposed by any GET endpoint.
    owner_token: str
