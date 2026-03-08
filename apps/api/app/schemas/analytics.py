from datetime import date
from pydantic import BaseModel


class DailyPostsOut(BaseModel):
    day: date
    count: int


class FollowerDeltaPointOut(BaseModel):
    snapshot_at: date
    delta: int


class FollowerDeltaSeriesOut(BaseModel):
    oauth_account_id: int
    platform: str
    display_name: str | None
    points: list[FollowerDeltaPointOut]


class UnfollowersAvailabilityOut(BaseModel):
    oauth_account_id: int
    platform: str
    available: bool
    note: str
