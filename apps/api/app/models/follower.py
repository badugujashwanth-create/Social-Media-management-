from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db import Base


class FollowerSnapshot(Base):
    __tablename__ = 'follower_snapshots'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    oauth_account_id: Mapped[int] = mapped_column(ForeignKey('oauth_accounts.id', ondelete='CASCADE'), index=True, nullable=False)
    follower_count: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class FollowerDelta(Base):
    __tablename__ = 'follower_deltas'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    oauth_account_id: Mapped[int] = mapped_column(ForeignKey('oauth_accounts.id', ondelete='CASCADE'), index=True, nullable=False)
    snapshot_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    delta: Mapped[int] = mapped_column(Integer, nullable=False)
