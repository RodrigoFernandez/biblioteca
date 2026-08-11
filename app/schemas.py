from datetime import datetime

from pydantic import BaseModel


class BookBase(BaseModel):
    title: str | None = None
    author: str | None = None
    publisher: str | None = None
    isbn: str | None = None


class BookResponse(BookBase):
    id: str
    image_path: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ImageProcessResponse(BaseModel):
    success: bool
    book: BookResponse | None = None
    message: str
