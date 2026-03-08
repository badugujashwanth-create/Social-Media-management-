from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
import httpx
from app.config import get_settings, Settings
from app.connectors.base import Connector, TokenResult
from app.crypto.token_vault import TokenVault
from app.models.oauth_account import OAuthAccount


class LinkedInConnector(Connector):
    platform_name = 'linkedin'

    def __init__(self):
        self.settings = get_settings()
        self.vault = TokenVault()

    def capabilities(self) -> dict[str, bool]:
        return {'supports_image': False, 'supports_link': True}

    def is_enabled(self, settings: Settings) -> bool:
        return bool(settings.linkedin_client_id and settings.linkedin_client_secret and settings.linkedin_redirect_uri)

    def get_oauth_authorize_url(self, state: str, code_challenge: str | None = None) -> str:
        params = urlencode(
            {
                'response_type': 'code',
                'client_id': self.settings.linkedin_client_id,
                'redirect_uri': self.settings.linkedin_redirect_uri,
                'state': state,
                'scope': 'openid profile w_member_social offline_access',
            }
        )
        return f'https://www.linkedin.com/oauth/v2/authorization?{params}'

    async def _fetch_member_identity(self, access_token: str) -> tuple[str, str | None]:
        headers = {'Authorization': f'Bearer {access_token}'}
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get('https://api.linkedin.com/v2/userinfo', headers=headers)
            if resp.status_code < 400:
                body = resp.json()
                member_id = str(body.get('sub') or '')
                if member_id:
                    name = body.get('name') or body.get('given_name')
                    return member_id, name

            fallback = await client.get(
                'https://api.linkedin.com/v2/me',
                headers={**headers, 'X-Restli-Protocol-Version': '2.0.0'},
                params={'projection': '(id,localizedFirstName,localizedLastName)'},
            )
            fallback.raise_for_status()
            fb = fallback.json()
            member_id = str(fb.get('id') or '')
            if not member_id:
                raise ValueError('LinkedIn member id is missing')
            first = str(fb.get('localizedFirstName') or '').strip()
            last = str(fb.get('localizedLastName') or '').strip()
            name = f'{first} {last}'.strip() or None
            return member_id, name

    async def exchange_code_for_token(self, code: str, code_verifier: str | None = None) -> TokenResult:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                'https://www.linkedin.com/oauth/v2/accessToken',
                data={
                    'grant_type': 'authorization_code',
                    'code': code,
                    'redirect_uri': self.settings.linkedin_redirect_uri,
                    'client_id': self.settings.linkedin_client_id,
                    'client_secret': self.settings.linkedin_client_secret,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        access_token = data['access_token']
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(data.get('expires_in', 3600)))
        member_id, member_name = await self._fetch_member_identity(access_token)
        author_urn = f'urn:li:person:{member_id}'
        return TokenResult(
            access_token=access_token,
            refresh_token=data.get('refresh_token'),
            expires_at=expires_at,
            scopes=data.get('scope') or 'openid profile w_member_social offline_access',
            external_account_id=member_id,
            display_name=member_name,
            meta_json={'author_urn': author_urn},
        )

    async def refresh_token_if_needed(self, account: OAuthAccount) -> OAuthAccount:
        if not account.expires_at or account.expires_at > datetime.now(timezone.utc):
            return account
        if not account.refresh_token_enc:
            return account

        refresh_token = self.vault.decrypt(account.refresh_token_enc)
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                'https://www.linkedin.com/oauth/v2/accessToken',
                data={
                    'grant_type': 'refresh_token',
                    'refresh_token': refresh_token,
                    'client_id': self.settings.linkedin_client_id,
                    'client_secret': self.settings.linkedin_client_secret,
                },
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
            raise ValueError('Invalid payload: image is not supported for LinkedIn in this MVP')

        access_token = self.vault.decrypt(account.access_token_enc)
        meta = account.meta_json or {}
        author = meta.get('organization_urn') or meta.get('author_urn') or f'urn:li:person:{account.external_account_id}'
        commentary = payload['text']

        share_content: dict = {
            'shareCommentary': {'text': commentary},
            'shareMediaCategory': 'NONE',
        }
        if payload.get('link_url'):
            share_content = {
                'shareCommentary': {'text': commentary},
                'shareMediaCategory': 'ARTICLE',
                'media': [{'status': 'READY', 'originalUrl': payload['link_url']}],
            }

        body = {
            'author': author,
            'lifecycleState': 'PUBLISHED',
            'specificContent': {'com.linkedin.ugc.ShareContent': share_content},
            'visibility': {'com.linkedin.ugc.MemberNetworkVisibility': 'PUBLIC'},
        }
        headers = {'Authorization': f'Bearer {access_token}', 'X-Restli-Protocol-Version': '2.0.0'}
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post('https://api.linkedin.com/v2/ugcPosts', json=body, headers=headers)
            resp.raise_for_status()
            post_id = resp.headers.get('x-restli-id')
            if post_id:
                return post_id
            payload_json = resp.json() if resp.content else {}
            if payload_json.get('id'):
                return str(payload_json['id'])
        raise ValueError('Platform error: LinkedIn did not return post id')

    async def get_follower_count(self, account: OAuthAccount) -> int | None:
        return None
