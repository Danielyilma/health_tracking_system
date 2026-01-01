from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel

class Notification(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True)
    message: str
    type: str # "Alert", "Reminder", "System"
    read: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class Reminder(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True)
    message: str
    schedule_time: datetime # When to trigger
    is_active: bool = True
