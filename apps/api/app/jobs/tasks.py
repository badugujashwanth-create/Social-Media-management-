import asyncio
from datetime import datetime, timezone
import time
import uuid
import httpx
from sqlalchemy import select
from app.config import get_settings
from app.db import SessionLocal
from app.models.post import PostTarget, Post
from app.models.oauth_account import OAuthAccount
from app.models.follower import FollowerSnapshot, FollowerDelta
from app.models.enums import PostTargetStatus
from app.connectors.registry import get_connectors


MAX_ATTEMPTS = 5
settings = get_settings()


def _terminal(status: str) -> bool:
    return status in {PostTargetStatus.success, PostTargetStatus.failed, PostTargetStatus.needs_reauth, PostTargetStatus.rate_limited}


def _use_dev_publish(connector, account: OAuthAccount) -> bool:
    if not settings.dev_mode:
        return False
    if connector is None:
        return True
    if hasattr(connector, 'is_enabled') and not connector.is_enabled(settings):
        return True
    source = (account.meta_json or {}).get('source')
    return source == 'manual_dev_mode'


def _dev_publish_result() -> str:
    time.sleep(1)
    return f"dev_{uuid.uuid4().hex}"


def _classify_publish_error(exc: Exception) -> tuple[str, str]:
    message = str(exc)
    lower = message.lower()

    if isinstance(exc, httpx.HTTPStatusError):
        status_code = exc.response.status_code
        if status_code in {401, 403}:
            return PostTargetStatus.needs_reauth, 'needs_reauth'
        if status_code == 429:
            return PostTargetStatus.rate_limited, 'rate_limited'
        if status_code in {400, 422}:
            return PostTargetStatus.failed, 'invalid_payload'
        return PostTargetStatus.failed, 'platform_error'

    if 'missing token' in lower or 'no token' in lower or ('access token' in lower and ('missing' in lower or 'invalid' in lower)):
        return PostTargetStatus.needs_reauth, 'needs_reauth'
    if '401' in lower or '403' in lower or 'unauthorized' in lower or 'forbidden' in lower or 'reauth' in lower:
        return PostTargetStatus.needs_reauth, 'needs_reauth'
    if '429' in lower or 'rate limit' in lower:
        return PostTargetStatus.rate_limited, 'rate_limited'
    if 'invalid payload' in lower or 'not supported' in lower or 'validation' in lower:
        return PostTargetStatus.failed, 'invalid_payload'
    return PostTargetStatus.failed, 'platform_error'


def _deterministic_dev_follower_count(account_id: int, day_ordinal: int) -> int:
    baseline = 200 + (account_id * 17)
    drift = ((day_ordinal * (account_id + 11)) % 33) - 8
    return max(1, baseline + drift)


def publish_task(post_target_id: int) -> None:
    db = SessionLocal()
    try:
        target = db.get(PostTarget, post_target_id)
        if not target or _terminal(target.status):
            return
        account = db.get(OAuthAccount, target.oauth_account_id)
        post = db.get(Post, target.post_id)
        if not account or not post:
            return

        target.status = PostTargetStatus.publishing
        target.attempts += 1
        target.last_attempt_at = datetime.now(timezone.utc)
        db.commit()

        connector = get_connectors().get(target.platform)
        try:
            if not account.access_token_enc:
                raise ValueError('Missing token for connected account')

            if _use_dev_publish(connector, account):
                external_id = _dev_publish_result()
            else:
                if connector is None:
                    raise ValueError(f'Connector not configured for platform: {target.platform}')
                refreshed = asyncio.run(connector.refresh_token_if_needed(account))
                if refreshed is not account:
                    account = refreshed
                db.commit()
                external_id = asyncio.run(
                    connector.publish_text_link(
                        account,
                        {'text': post.text, 'link_url': post.link_url, 'media_url': post.media_url},
                    )
                )

            target.status = PostTargetStatus.success
            target.external_post_id = external_id
            target.error_code = None
            target.error_message = None
        except Exception as exc:
            msg = str(exc)
            status, error_code = _classify_publish_error(exc)
            target.status = status
            target.error_code = error_code
            target.error_message = msg[:2000]
            transient = error_code in {'platform_error', 'rate_limited'}
            if target.attempts < MAX_ATTEMPTS and transient:
                target.status = PostTargetStatus.queued
                target.updated_at = datetime.now(timezone.utc)
                db.commit()
                raise
        target.updated_at = datetime.now(timezone.utc)
        db.commit()
    finally:
        db.close()


def snapshot_followers_task(user_id: int | None = None) -> None:
    db = SessionLocal()
    try:
        stmt = select(OAuthAccount)
        if user_id:
            stmt = stmt.where(OAuthAccount.user_id == user_id)
        accounts = db.scalars(stmt).all()
        connectors = get_connectors()
        today_ordinal = datetime.now(timezone.utc).date().toordinal()

        for acc in accounts:
            connector = connectors.get(acc.platform)
            count = None
            if connector and connector.is_enabled(settings):
                count = asyncio.run(connector.get_follower_count(acc))
            if count is None and settings.dev_mode:
                count = _deterministic_dev_follower_count(acc.id, today_ordinal)
            if count is None:
                continue

            snap = FollowerSnapshot(oauth_account_id=acc.id, follower_count=count)
            db.add(snap)
            db.flush()

            prev = db.scalars(
                select(FollowerSnapshot)
                .where(FollowerSnapshot.oauth_account_id == acc.id, FollowerSnapshot.id != snap.id)
                .order_by(FollowerSnapshot.snapshot_at.desc())
                .limit(1)
            ).first()
            delta = 0 if not prev else count - prev.follower_count
            db.add(FollowerDelta(oauth_account_id=acc.id, snapshot_at=snap.snapshot_at, delta=delta))
        db.commit()
    finally:
        db.close()
