from sqlalchemy import select
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from rq import Retry
from app.auth.deps import get_current_user
from app.connectors.registry import get_connectors
from app.db import get_db
from app.jobs.queue import publish_queue
from app.jobs.tasks import publish_task
from app.models.oauth_account import OAuthAccount
from app.models.post import Post, PostTarget
from app.models.enums import PostTargetStatus
from app.models.user import User
from app.schemas.posts import PublishIn, PostOut, PostTargetOut

router = APIRouter(prefix='/posts', tags=['posts'])


def _unsupported_targets(accounts: list[OAuthAccount], capability: str) -> list[OAuthAccount]:
    connectors = get_connectors()
    unsupported = []
    for account in accounts:
        connector = connectors.get(account.platform)
        supports = bool(connector and connector.capabilities().get(capability))
        if not supports:
            unsupported.append(account)
    return unsupported


def _create_post(payload: PublishIn, user: User, db: Session) -> PostOut:
    accounts_q = select(OAuthAccount).where(OAuthAccount.user_id == user.id)
    if payload.post_to_all:
        accounts = db.scalars(accounts_q).all()
    else:
        if not payload.target_account_ids:
            raise HTTPException(400, 'No target accounts selected')
        accounts = db.scalars(accounts_q.where(OAuthAccount.id.in_(payload.target_account_ids))).all()

    if not accounts:
        raise HTTPException(400, 'No connected target accounts found')

    if payload.media_url:
        unsupported = _unsupported_targets(accounts, 'supports_image')
        if unsupported:
            platforms = ', '.join(sorted({str(account.platform) for account in unsupported}))
            raise HTTPException(400, f'Image is not supported for selected targets: {platforms}')

    if payload.link_url:
        unsupported = _unsupported_targets(accounts, 'supports_link')
        if unsupported:
            platforms = ', '.join(sorted({str(account.platform) for account in unsupported}))
            raise HTTPException(400, f'Link is not supported for selected targets: {platforms}')

    post = Post(user_id=user.id, text=payload.text, link_url=str(payload.link_url) if payload.link_url else None, media_url=str(payload.media_url) if payload.media_url else None)
    db.add(post)
    db.commit()
    db.refresh(post)

    targets = []
    for acc in accounts:
        target = PostTarget(
            post_id=post.id,
            oauth_account_id=acc.id,
            platform=acc.platform,
            status=PostTargetStatus.queued,
        )
        db.add(target)
        db.flush()
        publish_queue.enqueue(
            publish_task,
            target.id,
            retry=Retry(max=5, interval=[10, 30, 90, 180]),
            job_timeout=120,
        )
        targets.append(target)

    db.commit()

    return PostOut(
        id=post.id,
        text=post.text,
        link_url=post.link_url,
        media_url=post.media_url,
        created_at=post.created_at,
        targets=[PostTargetOut.model_validate(t) for t in targets],
    )


@router.post('', response_model=PostOut)
def create_post(payload: PublishIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _create_post(payload, user, db)


@router.post('/publish', response_model=PostOut, include_in_schema=False)
def publish(payload: PublishIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _create_post(payload, user, db)


@router.get('', response_model=list[PostOut])
def list_posts(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    posts = db.scalars(select(Post).where(Post.user_id == user.id).order_by(Post.created_at.desc()).limit(50)).all()
    result = []
    for post in posts:
        targets = db.scalars(select(PostTarget).where(PostTarget.post_id == post.id).order_by(PostTarget.id)).all()
        result.append(
            PostOut(
                id=post.id,
                text=post.text,
                link_url=post.link_url,
                media_url=post.media_url,
                created_at=post.created_at,
                targets=[PostTargetOut.model_validate(t) for t in targets],
            )
        )
    return result


@router.get('/{post_id}', response_model=PostOut)
def get_post(post_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    post = db.get(Post, post_id)
    if not post or post.user_id != user.id:
        raise HTTPException(404, 'Post not found')
    targets = db.scalars(select(PostTarget).where(PostTarget.post_id == post.id).order_by(PostTarget.id)).all()
    return PostOut(
        id=post.id,
        text=post.text,
        link_url=post.link_url,
        media_url=post.media_url,
        created_at=post.created_at,
        targets=[PostTargetOut.model_validate(t) for t in targets],
    )
