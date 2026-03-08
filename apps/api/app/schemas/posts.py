from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl
from app.models.enums import Platform, PostTargetStatus


class PublishIn(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    link_url: HttpUrl | None = None
    media_url: HttpUrl | None = None
    target_account_ids: list[int] = Field(default_factory=list)
    post_to_all: bool = False


class PostTargetOut(BaseModel):
    id: int
    oauth_account_id: int
    platform: Platform
    status: PostTargetStatus
    error_code: str | None
    error_message: str | None
    external_post_id: str | None
    attempts: int
    updated_at: datetime

    model_config = {'from_attributes': True}


class PostOut(BaseModel):
    id: int
    text: str
    link_url: str | None
    media_url: str | None
    created_at: datetime
    targets: list[PostTargetOut]


class PostSummaryOut(BaseModel):
    id: int
    text: str
    created_at: datetime

    model_config = {'from_attributes': True}
