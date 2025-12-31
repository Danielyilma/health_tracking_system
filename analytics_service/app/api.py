from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.models import AnalyticsStats
from app.database import get_session

router = APIRouter()

@router.get("/stats/{username}", response_model=AnalyticsStats)
def get_stats(username: str, session: Session = Depends(get_session)):
    statement = select(AnalyticsStats).where(AnalyticsStats.username == username)
    result = session.exec(statement).first()
    if not result:
        raise HTTPException(status_code=404, detail="Stats not found")
    return result
