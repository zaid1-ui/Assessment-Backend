from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, ConfigDict

Status = Literal["todo", "in_progress", "done", "cancelled"]
Priority = Literal["low", "medium", "high", "urgent"]


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    status: Status = "todo"
    priority: Priority = "medium"
    project_id: int
    assignee_id: int | None = None
    due_date: datetime | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    status: Status | None = None
    priority: Priority | None = None
    assignee_id: int | None = None
    due_date: datetime | None = None


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    description: str | None
    status: str
    priority: str
    project_id: int
    assignee_id: int | None
    due_date: datetime | None
    created_at: datetime
