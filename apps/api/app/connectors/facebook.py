from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
import httpx
from app.config import get_settings, Settings
from app.connectors.base import Connector, TokenResult
from app.crypto.token_vault import TokenVault
from app.models.oauth_account import OAuthAccount


class FacebookConnector(Connector):
    platform_name = 'facebook'

    def __init__(self):
        self.settings = get_settings()
        self.vault = TokenVault()

    def capabilities(self) -> dict[str, bool]:
        return {'supports_image': False, 'supports_link': True}

    def is_enabled(self, settings: Settings) -> bool:
        return bool(settings.facebook_client_id and settings.facebook_client_secret and settings.facebook_redirect_uri)

    def get_oauth_authorize_url(self, state: str, code_challenge: str | None = None) -> str:
        params = urlencode(
            {
                'client_id': self.settings.facebook_client_id,
                'redirect_uri': self.settings.facebook_redirect_uri,
                'state': state,
                'scope': 'pages_manage_posts,pages_read_engagement,pages_show_list',
                'response_type': 'code',
            }
        )
        return f'https://www.facebook.com/v20.0/dialog/oauth?{params}'

    async def _exchange_for_user_token(self, code: str) -> tuple[str, int]:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(
                'https://graph.facebook.com/v20.0/oauth/access_token',
                params={
                    'client_id': self.settings.facebook_client_id,
                    'client_secret': self.settings.facebook_client_secret,
                    'redirect_uri': self.settings.facebook_redirect_uri,
                    'code': code,
                },
            )
            resp.raise_for_status()
            data = resp.json()
        return data['access_token'], int(data.get('expires_in', 3600))

    async def _exchange_long_lived_token(self, token: str) -> tuple[str, int]:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(
                'https://graph.facebook.com/v20.0/oauth/access_token',
                params={
                    'grant_type': 'fb_exchange_token',
                    'client_id': self.settings.facebook_client_id,
                    'client_secret': self.settings.facebook_client_secret,
                    'fb_exchange_token': token,
                },
            )
            if resp.status_code >= 400:
                return token, 3600
            data = resp.json()
        return data.get('access_token', token), int(data.get('expires_in', 3600))

    async def _get_me(self, user_access_token: str) -> dict:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(
                'https://graph.facebook.com/v20.0/me',
                params={'fields': 'id,name', 'access_token': user_access_token},
            )
            resp.raise_for_status()
            return resp.json()

    async def fetch_pages_for_user_token(self, user_access_token: str) -> list[dict]:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(
                'https://graph.facebook.com/v20.0/me/accounts',
                params={'fields': 'id,name,access_token', 'access_token': user_access_token},
            )
            resp.raise_for_status()
            body = resp.json()
        pages = []
        for raw in body.get('data', []):
            pages.append(
                {
                    'id': str(raw.get('id') or ''),
                    'name': str(raw.get('name') or raw.get('id') or ''),
                    'access_token': raw.get('access_token'),
                }
            )
        return [page for page in pages if page['id']]

    async def fetch_pages_for_account(self, account: OAuthAccount) -> list[dict]:
        encrypted_user_token = account.refresh_token_enc or account.access_token_enc
        user_access_token = self.vault.decrypt(encrypted_user_token)
        return await self.fetch_pages_for_user_token(user_access_token)

    async def exchange_code_for_token(self, code: str, code_verifier: str | None = None) -> TokenResult:
        user_token, _ = await self._exchange_for_user_token(code)
        long_lived_token, expires_in = await self._exchange_long_lived_token(user_token)
        me = await self._get_me(long_lived_token)
        pages = await self.fetch_pages_for_user_token(long_lived_token)
        if not pages:
            raise ValueError('No Facebook Pages available for this account')

        selected_page = pages[0]
        page_token = selected_page.get('access_token') or long_lived_token
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        page_meta = [{'id': page['id'], 'name': page['name'], 'has_access_token': bool(page.get('access_token'))} for page in pages]
        return TokenResult(
            access_token=page_token,
            refresh_token=long_lived_token,
            expires_at=expires_at,
            scopes='pages_manage_posts,pages_read_engagement,pages_show_list',
            external_account_id=selected_page['id'],
            display_name=selected_page['name'],
            meta_json={
                'facebook_user_id': str(me.get('id') or ''),
                'facebook_user_name': me.get('name'),
                'page_id': selected_page['id'],
                'page_name': selected_page['name'],
                'page_candidates': page_meta,
            },
        )

    async def refresh_token_if_needed(self, account: OAuthAccount) -> OAuthAccount:
        return account

    async def publish_text_link(self, account: OAuthAccount, payload: dict) -> str:
        if payload.get('media_url'):
            raise ValueError('Invalid payload: image is not supported for Facebook in this MVP')

        access_token = self.vault.decrypt(account.access_token_enc)
        page_id = account.external_account_id
        data = {'message': payload['text'], 'access_token': access_token}
        if payload.get('link_url'):
            data['link'] = payload['link_url']

        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(f'https://graph.facebook.com/v20.0/{page_id}/feed', data=data)
            resp.raise_for_status()
            body = resp.json()
        post_id = body.get('id')
        if not post_id:
            raise ValueError('Platform error: Facebook did not return post id')
        return post_id

    async def get_follower_count(self, account: OAuthAccount) -> int | None:
        access_token = self.vault.decrypt(account.access_token_enc)
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(
                f'https://graph.facebook.com/v20.0/{account.external_account_id}',
                params={'fields': 'followers_count', 'access_token': access_token},
            )
            if resp.status_code >= 400:
                return None
            body = resp.json()
        return body.get('followers_count')
