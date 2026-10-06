from core.db import get_items_collection

result = get_items_collection().delete_many({})
print(f"Deleted {result.deleted_count} document(s) from the 'items' collection.")
