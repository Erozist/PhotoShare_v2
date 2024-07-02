from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from src.schemas.user import UserResponse


class CommentCreate(BaseModel):
    content: str = Field(max_length=500)


class CommentUpdate(BaseModel):
    content: str = Field(max_length=500)


class CommentResponse(BaseModel):
    id: int
    content: str
    created_at: datetime
    updated_at: datetime
    user: UserResponse

    model_config = ConfigDict(from_attributes = True)
