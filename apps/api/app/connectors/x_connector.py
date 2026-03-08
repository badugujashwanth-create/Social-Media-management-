from app.config import Settings
from app.connectors.base import Connector, TokenResult
from app.models.oauth_account import OAuthAccount


class XAdapterConnector(Connector):
    platform_name = 'x'

    def capabilities(self) -> dict[str, bool]:
        return {'supports_image': False, 'supports_link': True}

    def is_enabled(self, settings: Settings) -> bool:
        return bool(settings.x_client_id and settings.x_client_secret and settings.x_redirect_uri)

    def get_oauth_authorize_url(self, state: str, code_challenge: str | None = None) -> str:
        raise NotImplementedError('X adapter placeholder. Current implementation lives in app/connectors/x.py.')

    async def exchange_code_for_token(self, code: str, code_verifier: str | None = None) -> TokenResult:
        raise NotImplementedError('X adapter placeholder. TODO: map provider response to SMCC contract.')

    async def refresh_token_if_needed(self, account: OAuthAccount) -> OAuthAccount:
        return account

    async def publish_text_link(self, account: OAuthAccount, payload: dict) -> str:
        raise NotImplementedError('X adapter placeholder. TODO: implement adapter publish logic.')

    async def get_follower_count(self, account: OAuthAccount) -> int | None:
        return None
