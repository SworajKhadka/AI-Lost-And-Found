import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"))
db = client["lost_and_found"]

result = db["items"].delete_many({})
print(f"Deleted {result.deleted_count} document(s) from the 'items' collection.")
