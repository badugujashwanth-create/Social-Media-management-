from app.config import Settings
from app.connectors.base import Connector, TokenResult
from app.models.oauth_account import OAuthAccount


class MetaConnector(Connector):
    platform_name = 'meta'

    def capabilities(self) -> dict[str, bool]:
        return {'supports_image': True, 'supports_link': True}

    def is_enabled(self, settings: Settings) -> bool:
        return False

    def get_oauth_authorize_url(self, state: str, code_challenge: str | None = None) -> str:
        raise NotImplementedError('Meta connector placeholder. TODO: implement unified Meta OAuth + publish flow.')

    async def exchange_code_for_token(self, code: str, code_verifier: str | None = None) -> TokenResult:
        raise NotImplementedError('Meta connector placeholder. TODO: exchange OAuth code for token.')

    async def refresh_token_if_needed(self, account: OAuthAccount) -> OAuthAccount:
        return account

    async def publish_text_link(self, account: OAuthAccount, payload: dict) -> str:
        raise NotImplementedError('Meta connector placeholder. TODO: implement publish adapter.')

    async def get_follower_count(self, account: OAuthAccount) -> int | None:
        return None
