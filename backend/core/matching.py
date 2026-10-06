"""Scoring logic that decides how likely two reports describe the same object.

Score (0-100) when both items have embeddings:
  up to 70  semantic similarity of title + description (Gemini embeddings)
  +20       same specific category (not "other"/"uncategorized")
  up to 10  shared keywords (+5 each, fuzzy: "iphone" ~ "phone")

Items created before embeddings existed fall back to the original
category + keyword-overlap scoring so nothing breaks during migration.
"""

import math

SIM_FLOOR = 0.55     # cosine similarity at or below this adds nothing
SIM_CEIL = 0.90      # cosine similarity at or above this adds the full 70
MIN_SEMANTIC_SCORE = 35
MIN_LEGACY_SCORE = 30
GENERIC_CATEGORIES = {"other", "uncategorized", ""}


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return dot / norm if norm else 0.0


def shared_keywords(a: list[str], b: list[str]) -> list[str]:
    """Keywords that match exactly or where one contains the other."""
    left = {k.lower().strip() for k in a or [] if k and k.strip()}
    right = {k.lower().strip() for k in b or [] if k and k.strip()}
    shared = []
    for kw in sorted(left):
        if any(kw == other or (len(kw) >= 3 and len(other) >= 3 and (kw in other or other in kw)) for other in right):
            shared.append(kw)
    return shared


def same_specific_category(a: dict, b: dict) -> bool:
    cat = (a.get("category") or "").strip()
    return cat not in GENERIC_CATEGORIES and cat == (b.get("category") or "").strip()


def score_pair(source: dict, candidate: dict) -> tuple[int, list[str]]:
    """Return (score, human-readable reasons) for a candidate match."""
    reasons: list[str] = []
    keywords = shared_keywords(source.get("keywords", []), candidate.get("keywords", []))

    if source.get("embedding") and candidate.get("embedding"):
        similarity = cosine_similarity(source["embedding"], candidate["embedding"])
        semantic = max(0.0, min(1.0, (similarity - SIM_FLOOR) / (SIM_CEIL - SIM_FLOOR)))
        score = semantic * 70
        if semantic > 0:
            reasons.append(f"Similar description ({round(similarity * 100)}% similarity)")
        if same_specific_category(source, candidate):
            score += 20
            reasons.append(f"Same category: {source['category']}")
        if keywords:
            score += min(len(keywords) * 5, 10)
            reasons.append("Shared keywords: " + ", ".join(keywords))
        final = min(round(score), 100)
        return (final if final >= MIN_SEMANTIC_SCORE else 0), reasons

    # Legacy scoring for items without embeddings
    score = 0
    category = source.get("category") or ""
    if category not in {"", "uncategorized"} and category == candidate.get("category"):
        score += 40
        reasons.append(f"Same category: {source['category']}")
    if keywords:
        score += min(len(keywords) * 15, 60)
        reasons.append("Shared keywords: " + ", ".join(keywords))
    final = min(score, 100)
    return (final if final >= MIN_LEGACY_SCORE else 0), reasons
