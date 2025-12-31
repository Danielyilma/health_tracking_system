from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel

class HealthRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    steps: int
    sleep_hours: float
    weight: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class HealthRecordUpdate(SQLModel):
    steps: Optional[int] = None
    sleep_hours: Optional[float] = None
    weight: Optional[float] = None
