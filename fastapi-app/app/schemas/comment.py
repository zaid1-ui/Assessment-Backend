from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class CommentCreate(BaseModel):
    content: str = Field(min_length=1)
    task_id: int
    author_id: int


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    content: str
    task_id: int
    author_id: int
    created_at: datetime
