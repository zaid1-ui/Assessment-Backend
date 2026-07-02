from typing import Generic, TypeVar, Optional
from pydantic import BaseModel

T = TypeVar("T")


class Meta(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Success"
    data: Optional[T] = None
    meta: Optional[Meta] = None
