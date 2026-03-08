from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
import httpx
from app.config import get_settings, Settings
from app.connectors.base import Connector, TokenResult
from app.crypto.token_vault import TokenVault
from app.models.oauth_account import OAuthAccount


class XConnector(Connector):
    platform_name = 'x'

    def __init__(self):
        self.settings = get_settings()
        self.vault = TokenVault()

    def capabilities(self) -> dict[str, bool]:
        return {'supports_image': False, 'supports_link': True}

    def is_enabled(self, settings: Settings) -> bool:
        return bool(settings.x_client_id and settings.x_client_secret and settings.x_redirect_uri)

    def get_oauth_authorize_url(self, state: str, code_challenge: str | None = None) -> str:
        if not code_challenge:
            raise ValueError('PKCE code challenge is required for X OAuth2 flow')
        params = urlencode(
            {
                'response_type': 'code',
                'client_id': self.settings.x_client_id,
                'redirect_uri': self.settings.x_redirect_uri,
                'scope': 'tweet.write users.read offline.access',
                'state': state,
                'code_challenge': code_challenge,
                'code_challenge_method': 'S256',
            }
        )
        return f'https://twitter.com/i/oauth2/authorize?{params}'

    async def _fetch_user(self, access_token: str) -> dict:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(
                'https://api.x.com/2/users/me',
                headers={'Authorization': f'Bearer {access_token}'},
            )
            resp.raise_for_status()
            return resp.json().get('data', {})

    async def exchange_code_for_token(self, code: str, code_verifier: str | None = None) -> TokenResult:
        if not code_verifier:
            raise ValueError('PKCE code verifier missing for X OAuth callback')

        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                'https://api.x.com/2/oauth2/token',
                data={
                    'grant_type': 'authorization_code',
                    'code': code,
                    'redirect_uri': self.settings.x_redirect_uri,
                    'client_id': self.settings.x_client_id,
                    'code_verifier': code_verifier,
                },
                auth=(self.settings.x_client_id or '', self.settings.x_client_secret or ''),
            )
            resp.raise_for_status()
            data = resp.json()

        access_token = data['access_token']
        user = await self._fetch_user(access_token)
        user_id = str(user.get('id') or '')
        if not user_id:
            raise ValueError('X user id missing from OAuth profile response')
        display_name = user.get('name') or user.get('username')

        expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(data.get('expires_in', 3600)))
        return TokenResult(
            access_token=access_token,
            refresh_token=data.get('refresh_token'),
            expires_at=expires_at,
            scopes=data.get('scope'),
            external_account_id=user_id,
            display_name=display_name,
            meta_json={'x_user_id': user_id, 'x_username': user.get('username')},
        )

    async def refresh_token_if_needed(self, account: OAuthAccount) -> OAuthAccount:
        if not account.expires_at or account.expires_at > datetime.now(timezone.utc):
            return account
        if not account.refresh_token_enc:
            return account

        refresh_token = self.vault.decrypt(account.refresh_token_enc)
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                'https://api.x.com/2/oauth2/token',
                data={
                    'grant_type': 'refresh_token',
                    'refresh_token': refresh_token,
                    'client_id': self.settings.x_client_id,
                },
                auth=(self.settings.x_client_id or '', self.settings.x_client_secret or ''),
            )
            if resp.status_code >= 400:
                return account
            data = resp.json()

        account.access_token_enc = self.vault.encrypt(data['access_token'])
        if data.get('refresh_token'):
            account.refresh_token_enc = self.vault.encrypt(data['refresh_token'])
        account.expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(data.get('expires_in', 3600)))
        return account

    async def publish_text_link(self, account: OAuthAccount, payload: dict) -> str:
        if payload.get('media_url'):
            raise ValueError('Invalid payload: image is not supported for X in this MVP')

        access_token = self.vault.decrypt(account.access_token_enc)
        text = payload['text'] + (f" {payload.get('link_url')}" if payload.get('link_url') else '')
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                'https://api.x.com/2/tweets',
                json={'text': text},
                headers={'Authorization': f'Bearer {access_token}'},
            )
            resp.raise_for_status()
            data = resp.json()
        post_id = data.get('data', {}).get('id')
        if not post_id:
            raise ValueError('Platform error: X did not return post id')
        return post_id

    async def get_follower_count(self, account: OAuthAccount) -> int | None:
        return None
