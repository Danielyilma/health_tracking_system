from fastapi import FastAPI
from app.database import create_db_and_tables
from app.api import router as auth_router

app = FastAPI(title="Auth Service")

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/health")
def health_check():
    return {"status": "ok"}

app.include_router(auth_router)
