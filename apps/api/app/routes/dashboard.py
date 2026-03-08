from datetime import datetime, timezone
from sqlalchemy import select
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.auth.deps import get_current_user
from app.db import get_db
from app.models.oauth_account import OAuthAccount
from app.models.post import Post, PostTarget
from app.models.user import User

router = APIRouter(prefix='/dashboard', tags=['dashboard'])


@router.get('')
def overview(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    accounts = db.scalars(select(OAuthAccount).where(OAuthAccount.user_id == user.id)).all()
    posts = db.scalars(select(Post).where(Post.user_id == user.id).order_by(Post.created_at.desc()).limit(10)).all()

    post_list = []
    for p in posts:
        targets = db.scalars(select(PostTarget).where(PostTarget.post_id == p.id)).all()
        post_list.append(
            {
                'id': p.id,
                'text': p.text,
                'created_at': p.created_at,
                'targets': [
                    {
                        'id': t.id,
                        'platform': t.platform,
                        'status': t.status,
                        'external_post_id': t.external_post_id,
                    }
                    for t in targets
                ],
            }
        )

    return {
        'accounts': [
            {
                'id': a.id,
                'platform': a.platform,
                'display_name': a.display_name,
                'updated_at': a.updated_at,
                'token_health': 'ok' if not a.expires_at or a.expires_at > datetime.now(timezone.utc) else 'expiring_or_expired',
            }
            for a in accounts
        ],
        'recent_posts': post_list,
    }
