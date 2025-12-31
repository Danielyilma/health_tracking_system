from fastapi import FastAPI
from app.database import create_db_and_tables
from app.api import router as analytics_router

app = FastAPI(title="Analytics Service")

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/health")
def health_check():
    return {"status": "ok"}

app.include_router(analytics_router)
