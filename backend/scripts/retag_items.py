"""Repair existing items: re-run Gemini tagging and add missing embeddings.

Fixes items saved as "uncategorized" (when Gemini was unreachable) and
items created before semantic matching existed.

Usage (from the backend/ folder, with .env configured):
    python -m scripts.retag_items --dry-run   # show what would change
    python -m scripts.retag_items             # apply
    python -m scripts.retag_items --all       # re-tag every item
"""

import argparse
import time

from core.ai import FALLBACK_CATEGORY, embed_text, extract_item_metadata, item_embedding_text
from core.db import get_items_collection


def needs_retag(item: dict) -> bool:
    return (
        item.get("ai_status") == "pending"
        or item.get("category") in (None, "", FALLBACK_CATEGORY)
        or not item.get("keywords")
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="report changes without writing")
    parser.add_argument("--all", action="store_true", help="re-tag and re-embed every item")
    parser.add_argument("--delay", type=float, default=1.0, help="seconds between items (free-tier rate limits)")
    args = parser.parse_args()

    collection = get_items_collection()
    retagged = embedded = failed = 0

    for item in collection.find({}, {"owner_token": 0}):
        label = f"{item['_id']} '{item.get('title', '')}'"
        update: dict = {}
        retag = args.all or needs_retag(item)
        reembed = args.all or retag or not item.get("embedding")

        if not (retag or reembed):
            continue
        if args.dry_run:
            print(f"[dry-run] {label}: retag={retag} embed={reembed}")
            continue

        if retag:
            metadata = extract_item_metadata(item.get("title", ""), item.get("description", ""))
            if metadata:
                update.update(metadata, ai_status="ok")
                item.update(metadata)
                retagged += 1
            else:
                failed += 1
                print(f"  ! tagging failed for {label}")

        if reembed:
            vector = embed_text(item_embedding_text(item))
            if vector:
                update["embedding"] = vector
                embedded += 1
            else:
                failed += 1
                print(f"  ! embedding failed for {label}")

        if update:
            collection.update_one({"_id": item["_id"]}, {"$set": update})
            print(f"  ✓ {label} -> {item.get('category')} {item.get('keywords')}")
        time.sleep(args.delay)

    if not args.dry_run:
        print(f"\nDone. Re-tagged: {retagged}, embedded: {embedded}, failures: {failed}")


if __name__ == "__main__":
    main()
