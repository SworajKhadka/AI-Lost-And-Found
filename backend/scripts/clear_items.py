"""Delete EVERY item from the database. Intended for local/dev databases.

Usage (from the backend/ folder):
    python -m scripts.clear_items --yes
"""

import argparse

from core.db import get_items_collection


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--yes", action="store_true", help="confirm you really want to wipe the collection")
    args = parser.parse_args()

    collection = get_items_collection()
    if not args.yes:
        count = collection.count_documents({})
        print(f"This would delete {count} item(s). Re-run with --yes to confirm.")
        return

    result = collection.delete_many({})
    print(f"Deleted {result.deleted_count} document(s) from the 'items' collection.")


if __name__ == "__main__":
    main()
