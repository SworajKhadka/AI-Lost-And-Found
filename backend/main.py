from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from routes.items import router as items_router
from routes.matches import router as matches_router

load_dotenv()

app = FastAPI(title="AI Lost and Found API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(items_router, prefix="/items", tags=["items"])
app.include_router(matches_router, prefix="/matches", tags=["matches"])


@app.get("/")
def root():
    return {"message": "AI Lost and Found API is running"}
