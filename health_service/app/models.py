from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel

class HealthRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    steps: Optional[int] = None
    sleep_hours: Optional[float] = None
    weight: Optional[float] = None
    heart_rate: Optional[int] = None
    blood_pressure: Optional[str] = None
    blood_sugar: Optional[float] = None
    body_temperature: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class HealthRecordCreate(SQLModel):
    steps: Optional[int] = None
    sleep_hours: Optional[float] = None
    weight: Optional[float] = None
    heart_rate: Optional[int] = None
    blood_pressure: Optional[str] = None
    blood_sugar: Optional[float] = None
    body_temperature: Optional[float] = None

class HealthRecordUpdate(SQLModel):
    steps: Optional[int] = None
    sleep_hours: Optional[float] = None
    weight: Optional[float] = None
    heart_rate: Optional[int] = None
    blood_pressure: Optional[str] = None
    blood_sugar: Optional[float] = None
    body_temperature: Optional[float] = None
