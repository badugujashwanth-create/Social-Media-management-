from __future__ import annotations

from typing import Any
import httpx
from app.config import Settings, get_settings
from app.connectors.base import Connector, TokenResult
from app.models.oauth_account import OAuthAccount


class AyrshareConnector(Connector):
    platform_name = 'ayrshare'
    api_base_url = 'https://api.ayrshare.com/api'

    def __init__(self):
        self.settings = get_settings()

    def capabilities(self) -> dict[str, bool]:
        return {'supports_image': True, 'supports_link': True}

    def is_enabled(self, settings: Settings) -> bool:
        return bool(settings.ayrshare_api_key)

    def get_oauth_authorize_url(self, state: str, code_challenge: str | None = None) -> str:
        raise NotImplementedError('Ayrshare connector uses API key auth. Configure AYRSHARE_API_KEY and account metadata.')

    async def exchange_code_for_token(self, code: str, code_verifier: str | None = None) -> TokenResult:
        raise NotImplementedError('Ayrshare connector does not use OAuth code exchange.')

    async def refresh_token_if_needed(self, account: OAuthAccount) -> OAuthAccount:
        return account

    def _platforms(self, account: OAuthAccount, payload: dict[str, Any]) -> list[str] | None:
        source = payload.get('platforms')
        if source is None:
            meta = account.meta_json or {}
            source = meta.get('ayrshare_platforms') or meta.get('platforms')

        if isinstance(source, str):
            return [source]
        if isinstance(source, list):
            values = [str(item).strip() for item in source if str(item).strip()]
            return values or None
        return None

    async def publish_text_link(self, account: OAuthAccount, payload: dict[str, Any]) -> str:
        if not self.settings.ayrshare_api_key:
            raise ValueError('Ayrshare connector disabled: AYRSHARE_API_KEY is not set')

        text = str(payload.get('text') or '').strip()
        if not text:
            raise ValueError('Invalid payload: text is required')

        link_url = payload.get('link_url')
        post_text = f'{text} {link_url}'.strip() if link_url else text
        body: dict[str, Any] = {'post': post_text}

        media_url = payload.get('media_url')
        if media_url:
            body['mediaUrls'] = [str(media_url)]

        platforms = self._platforms(account, payload)
        if platforms:
            body['platforms'] = platforms

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.settings.ayrshare_api_key}',
        }
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(f'{self.api_base_url}/post', json=body, headers=headers)
            response.raise_for_status()
            data = response.json()

        post_id = data.get('id') or data.get('refId')
        if not post_id:
            post_ids = data.get('postIds')
            if isinstance(post_ids, dict) and post_ids:
                key = next(iter(post_ids))
                post_id = f'{key}:{post_ids[key]}'
            elif isinstance(post_ids, list) and post_ids:
                post_id = str(post_ids[0])

        if not post_id:
            raise ValueError('Platform error: Ayrshare did not return post id')
        return str(post_id)

    async def get_follower_count(self, account: OAuthAccount) -> int | None:
        return None
