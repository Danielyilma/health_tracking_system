from typing import Optional
from sqlmodel import Field, SQLModel

class AnalyticsStats(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True)
    total_steps: int = 0
    record_count: int = 0
    average_steps: float = 0.0
