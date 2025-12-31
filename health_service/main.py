from fastapi import FastAPI
from app.database import create_db_and_tables
from app.api import router as health_router

app = FastAPI(title="Health Data Service")

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/health")
def health_check():
    return {"status": "ok"}

app.include_router(health_router)
