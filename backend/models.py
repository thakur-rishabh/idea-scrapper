from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime, timezone

class Idea(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    summary: str
    source_url: str = Field(index=True, unique=True)
    original_text: str
    score: int
    target_audience: Optional[str] = None
    status: str = Field(default="pending") # pending, approved, rejected, starred
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
