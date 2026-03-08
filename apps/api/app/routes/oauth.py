import base64
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.auth.deps import get_current_user
from app.config import get_settings
from app.connectors.facebook import FacebookConnector
from app.connectors.registry import get_connectors
from app.crypto.token_vault import TokenVault
from app.db import get_db
from app.models.oauth_account import OAuthAccount
from app.models.oauth_state import OAuthState
from app.models.user import User
from app.schemas.accounts import FacebookPageOut, OAuthAccountOut, OAuthStartOut

router = APIRouter(prefix='/oauth', tags=['accounts'])
settings = get_settings()
vault = TokenVault()

STATE_TTL_MINUTES = 10


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _to_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _get_connector(platform: str):
    connector = get_connectors().get(platform)
    if not connector:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Connector not found')
    if not connector.is_enabled(settings):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Connector not enabled')
    return connector


def _make_redirect_url(params: dict[str, str]) -> str:
    base = f"{settings.app_public_url.rstrip('/')}/accounts"
    return f'{base}?{urlencode(params)}'


def _generate_pkce_verifier() -> str:
    return secrets.token_urlsafe(64)[:128]


def _generate_code_challenge(code_verifier: str) -> str:
    digest = hashlib.sha256(code_verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).decode().rstrip('=')


def _issue_state(db: Session, user_id: int, platform: str, code_verifier: str | None = None) -> OAuthState:
    record = OAuthState(
        user_id=user_id,
        platform=platform,
        state=secrets.token_urlsafe(32),
        code_verifier=code_verifier,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def _consume_state(db: Session, platform: str, state_value: str) -> OAuthState:
    state = db.scalar(select(OAuthState).where(OAuthState.state == state_value, OAuthState.platform == platform))
    if not state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid oauth state')
    if state.used_at:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='OAuth state already used')
    created_at = _to_utc(state.created_at)
    if created_at < _now_utc() - timedelta(minutes=STATE_TTL_MINUTES):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='OAuth state expired')

    state.used_at = _now_utc()
    db.commit()
    db.refresh(state)
    return state


def _upsert_account(db: Session, state: OAuthState, platform: str, token_result) -> OAuthAccount:
    account = db.scalar(
        select(OAuthAccount).where(
            OAuthAccount.user_id == state.user_id,
            OAuthAccount.platform == platform,
            OAuthAccount.external_account_id == token_result.external_account_id,
        )
    )
    if account:
        account.display_name = token_result.display_name
        account.access_token_enc = vault.encrypt(token_result.access_token)
        if token_result.refresh_token:
            account.refresh_token_enc = vault.encrypt(token_result.refresh_token)
        account.expires_at = token_result.expires_at
        account.scopes = token_result.scopes
        account.meta_json = token_result.meta_json
    else:
        account = OAuthAccount(
            user_id=state.user_id,
            platform=platform,
            display_name=token_result.display_name,
            external_account_id=token_result.external_account_id,
            access_token_enc=vault.encrypt(token_result.access_token),
            refresh_token_enc=vault.encrypt(token_result.refresh_token) if token_result.refresh_token else None,
            expires_at=token_result.expires_at,
            scopes=token_result.scopes,
            meta_json=token_result.meta_json,
        )
        db.add(account)

    db.commit()
    db.refresh(account)
    return account


def _account_out(account: OAuthAccount) -> OAuthAccountOut:
    connector = get_connectors().get(account.platform)
    capabilities = connector.capabilities() if connector else {'supports_image': False, 'supports_link': True}
    return OAuthAccountOut(
        id=account.id,
        platform=account.platform,
        display_name=account.display_name,
        external_account_id=account.external_account_id,
        expires_at=account.expires_at,
        scopes=account.scopes,
        meta_json=account.meta_json,
        capabilities=capabilities,
        updated_at=account.updated_at,
    )


@router.get('/{platform}/start', response_model=OAuthStartOut)
def oauth_start(platform: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    connector = _get_connector(platform)
    code_verifier = None
    code_challenge = None
    if platform == 'x':
        code_verifier = _generate_pkce_verifier()
        code_challenge = _generate_code_challenge(code_verifier)

    state = _issue_state(db, user.id, platform, code_verifier=code_verifier)
    redirect_url = connector.get_oauth_authorize_url(state.state, code_challenge=code_challenge)
    return OAuthStartOut(redirect_url=redirect_url)


@router.get('/{platform}/callback')
async def oauth_callback(
    platform: str,
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db),
):
    connector = _get_connector(platform)
    state_row = _consume_state(db, platform, state)
    token_result = await connector.exchange_code_for_token(code, code_verifier=state_row.code_verifier)
    account = _upsert_account(db, state_row, platform, token_result)

    params = {'connected': '1', 'platform': platform, 'account_id': str(account.id)}
    candidates = (account.meta_json or {}).get('page_candidates') if platform == 'facebook' else None
    if isinstance(candidates, list) and len(candidates) > 1:
        params['needs_page_select'] = '1'
    return RedirectResponse(url=_make_redirect_url(params), status_code=status.HTTP_302_FOUND)


@router.get('/facebook/pages', response_model=list[FacebookPageOut])
async def list_facebook_pages(
    account_id: int | None = Query(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    connector = _get_connector('facebook')
    if not isinstance(connector, FacebookConnector):
        raise HTTPException(status_code=500, detail='Facebook connector unavailable')

    query = select(OAuthAccount).where(OAuthAccount.user_id == user.id, OAuthAccount.platform == 'facebook')
    if account_id:
        query = query.where(OAuthAccount.id == account_id)
    account = db.scalar(query.order_by(OAuthAccount.updated_at.desc()))
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Facebook account not found')

    try:
        pages = await connector.fetch_pages_for_account(account)
    except Exception:
        pages = []

    if not pages:
        candidates = (account.meta_json or {}).get('page_candidates') or []
        for raw in candidates:
            if not isinstance(raw, dict) or not raw.get('id'):
                continue
            pages.append(
                {
                    'id': str(raw.get('id')),
                    'name': str(raw.get('name') or raw.get('id')),
                    'access_token': None,
                }
            )
    return [FacebookPageOut.model_validate(page) for page in pages]


class FacebookPageSelectIn(BaseModel):
    account_id: int = Field(gt=0)
    page_id: str = Field(min_length=1)


@router.post('/facebook/pages/select', response_model=OAuthAccountOut)
async def select_facebook_page(
    payload: FacebookPageSelectIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    connector = _get_connector('facebook')
    if not isinstance(connector, FacebookConnector):
        raise HTTPException(status_code=500, detail='Facebook connector unavailable')

    account = db.get(OAuthAccount, payload.account_id)
    if not account or account.user_id != user.id or account.platform != 'facebook':
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Facebook account not found')

    try:
        pages = await connector.fetch_pages_for_account(account)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Unable to fetch pages for this account') from exc
    selected_page = next((page for page in pages if str(page.get('id')) == payload.page_id), None)
    if not selected_page:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Page not found')
    if not selected_page.get('access_token'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Selected page did not include access token')

    account.external_account_id = str(selected_page['id'])
    account.display_name = str(selected_page.get('name') or selected_page['id'])
    account.access_token_enc = vault.encrypt(selected_page['access_token'])
    meta = dict(account.meta_json or {})
    meta['page_id'] = account.external_account_id
    meta['page_name'] = account.display_name
    meta['page_candidates'] = [
        {'id': str(page.get('id')), 'name': str(page.get('name') or page.get('id')), 'has_access_token': bool(page.get('access_token'))}
        for page in pages
    ]
    account.meta_json = meta
    db.commit()
    db.refresh(account)
    return _account_out(account)
