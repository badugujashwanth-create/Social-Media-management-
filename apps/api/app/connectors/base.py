from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from app.config import Settings
from app.models.oauth_account import OAuthAccount


@dataclass
class TokenResult:
    access_token: str
    refresh_token: str | None = None
    expires_at: datetime | None = None
    scopes: str | None = None
    external_account_id: str = 'unknown'
    display_name: str | None = None
    meta_json: dict[str, Any] | None = None


class Connector(ABC):
    platform_name: str

    def capabilities(self) -> dict[str, bool]:
        return {'supports_image': False, 'supports_link': True}

    @abstractmethod
    def is_enabled(self, settings: Settings) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get_oauth_authorize_url(self, state: str, code_challenge: str | None = None) -> str:
        raise NotImplementedError

    @abstractmethod
    async def exchange_code_for_token(self, code: str, code_verifier: str | None = None) -> TokenResult:
        raise NotImplementedError

    @abstractmethod
    async def refresh_token_if_needed(self, account: OAuthAccount) -> OAuthAccount:
        raise NotImplementedError

    @abstractmethod
    async def publish_text_link(self, account: OAuthAccount, payload: dict[str, Any]) -> str:
        raise NotImplementedError

    @abstractmethod
    async def get_follower_count(self, account: OAuthAccount) -> int | None:
        raise NotImplementedError

    async def get_follower_list(self, account: OAuthAccount) -> list[str] | None:
        return None
