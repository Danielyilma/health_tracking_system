from datetime import date as dt_date, datetime
from typing import Optional
from sqlmodel import Field, SQLModel

class AnalyticsStats(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    total_steps: int = 0
    record_count: int = 0
    average_steps: float = 0.0

class DailyHealthStats(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True)
    date: dt_date = Field(index=True)
    
    # Daily Aggregates
    total_steps: int = 0
    sleep_hours: float = 0.0
    
    # Heart Rate Stats
    avg_heart_rate: float = 0.0
    min_heart_rate: Optional[int] = None
    max_heart_rate: Optional[int] = None
    heart_rate_count: int = 0 # Helper for avg calculation
    
    # Weight (taking the latest or avg)
    avg_weight: float = 0.0
    weight_count: int = 0

class HealthInsight(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    type: str # "Trend", "Anomaly", "Achievement", "Recommendation"
    severity: str # "INFO", "WARNING", "CRITICAL"
    message: str
