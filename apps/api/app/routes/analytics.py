from sqlalchemy import func, select
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.auth.deps import get_current_user
from app.connectors.base import Connector
from app.connectors.registry import get_connectors
from app.db import get_db
from app.jobs.tasks import snapshot_followers_task
from app.models.follower import FollowerDelta
from app.models.oauth_account import OAuthAccount
from app.models.post import Post
from app.models.user import User
from app.schemas.analytics import DailyPostsOut, FollowerDeltaPointOut, FollowerDeltaSeriesOut, UnfollowersAvailabilityOut

router = APIRouter(prefix='/analytics', tags=['analytics'])


@router.get('/daily-posts', response_model=list[DailyPostsOut])
def daily_posts(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.execute(
        select(func.date(Post.created_at).label('day'), func.count(Post.id).label('count'))
        .where(Post.user_id == user.id)
        .group_by(func.date(Post.created_at))
        .order_by(func.date(Post.created_at).desc())
        .limit(30)
    ).all()
    return [DailyPostsOut(day=r.day, count=r.count) for r in rows]


@router.get('/follower-deltas', response_model=list[FollowerDeltaSeriesOut])
def follower_deltas(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.execute(
        select(FollowerDelta, OAuthAccount)
        .join(OAuthAccount, OAuthAccount.id == FollowerDelta.oauth_account_id)
        .where(OAuthAccount.user_id == user.id)
        .order_by(OAuthAccount.id.asc(), FollowerDelta.snapshot_at.asc())
    ).all()
    series_by_account: dict[int, FollowerDeltaSeriesOut] = {}
    for fd, acc in rows:
        if acc.id not in series_by_account:
            series_by_account[acc.id] = FollowerDeltaSeriesOut(
                oauth_account_id=acc.id,
                platform=acc.platform,
                display_name=acc.display_name,
                points=[],
            )
        series_by_account[acc.id].points.append(FollowerDeltaPointOut(snapshot_at=fd.snapshot_at.date(), delta=fd.delta))
    return list(series_by_account.values())


@router.get('/unfollowers-availability', response_model=list[UnfollowersAvailabilityOut])
def unfollowers_availability(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    connectors = get_connectors()
    accounts = db.scalars(select(OAuthAccount).where(OAuthAccount.user_id == user.id)).all()
    output = []
    for acc in accounts:
        connector = connectors.get(acc.platform)
        supports = bool(connector and connector.__class__.get_follower_list is not Connector.get_follower_list)
        output.append(
            UnfollowersAvailabilityOut(
                oauth_account_id=acc.id,
                platform=acc.platform,
                available=supports,
                note='Supported by official API' if supports else 'Not available on this platform/API',
            )
        )
    return output


@router.post('/snapshot')
def trigger_snapshot(user: User = Depends(get_current_user)):
    snapshot_followers_task(user.id)
    return {'status': 'ok'}


@router.post('/snapshot-followers', include_in_schema=False)
def trigger_snapshot_legacy(user: User = Depends(get_current_user)):
    snapshot_followers_task(user.id)
    return {'status': 'ok'}
