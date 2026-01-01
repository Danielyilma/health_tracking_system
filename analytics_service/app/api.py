from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.models import AnalyticsStats, DailyHealthStats, HealthInsight
from app.database import get_session

router = APIRouter()

@router.get("/stats/{username}", response_model=AnalyticsStats)
def get_stats(username: str, session: Session = Depends(get_session)):
    statement = select(AnalyticsStats).where(AnalyticsStats.username == username)
    result = session.exec(statement).first()
    if not result:
        raise HTTPException(status_code=404, detail="Stats not found")
    return result

@router.get("/stats/daily/{username}", response_model=List[DailyHealthStats])
def get_daily_stats(username: str, session: Session = Depends(get_session)):
    statement = select(DailyHealthStats).where(DailyHealthStats.username == username).order_by(DailyHealthStats.date.desc())
    return session.exec(statement).all()

@router.get("/insights/{username}", response_model=List[HealthInsight])
def get_insights(username: str, session: Session = Depends(get_session)):
    statement = select(HealthInsight).where(HealthInsight.username == username).order_by(HealthInsight.timestamp.desc())
    return session.exec(statement).all()

@router.get("/summary/{username}", response_model=dict)
def get_summary(username: str, session: Session = Depends(get_session)):
    from app.engine import generate_summary_text
    summary_text = generate_summary_text(username, session)
    return {"summary": summary_text}
