from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.auth.deps import get_current_user
from app.config import get_settings
from app.connectors.registry import get_connectors
from app.crypto.token_vault import TokenVault
from app.db import get_db
from app.models.oauth_account import OAuthAccount
from app.models.user import User
from app.schemas.accounts import OAuthAccountOut, ManualTokenConnectIn

router = APIRouter(prefix='/accounts', tags=['accounts'])
settings = get_settings()
vault = TokenVault()


def _account_out(account: OAuthAccount) -> OAuthAccountOut:
    connectors = get_connectors()
    connector = connectors.get(account.platform)
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


@router.get('', response_model=list[OAuthAccountOut])
def list_accounts(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    accounts = db.scalars(select(OAuthAccount).where(OAuthAccount.user_id == user.id).order_by(OAuthAccount.created_at.desc())).all()
    return [_account_out(account) for account in accounts]


def _create_dev_account(payload: ManualTokenConnectIn, user: User, db: Session) -> OAuthAccountOut:
    if not settings.dev_mode:
        raise HTTPException(status_code=403, detail='Developer mode is disabled')

    account = OAuthAccount(
        user_id=user.id,
        platform=payload.platform,
        display_name=payload.display_name,
        external_account_id=payload.external_account_id,
        access_token_enc=vault.encrypt(payload.access_token),
        refresh_token_enc=vault.encrypt(payload.refresh_token) if payload.refresh_token else None,
        scopes=payload.scopes,
        meta_json={'source': 'manual_dev_mode'},
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return _account_out(account)


@router.post('/dev', response_model=OAuthAccountOut)
def connect_dev(payload: ManualTokenConnectIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _create_dev_account(payload, user, db)


@router.post('/manual', response_model=OAuthAccountOut, include_in_schema=False)
def connect_manual(payload: ManualTokenConnectIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _create_dev_account(payload, user, db)


@router.delete('/{account_id}', status_code=204)
def disconnect(account_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    account = db.get(OAuthAccount, account_id)
    if not account or account.user_id != user.id:
        raise HTTPException(404, 'Account not found')
    db.delete(account)
    db.commit()
    return None
