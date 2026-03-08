from app.config import Settings
from app.connectors.base import Connector, TokenResult
from app.models.oauth_account import OAuthAccount


class InstagramStubConnector(Connector):
    platform_name = 'instagram'

    def capabilities(self) -> dict[str, bool]:
        return {'supports_image': False, 'supports_link': False}

    def is_enabled(self, settings: Settings) -> bool:
        return settings.dev_mode

    def get_oauth_authorize_url(self, state: str, code_challenge: str | None = None) -> str:
        return f'/todo/instagram-auth?state={state}'

    async def exchange_code_for_token(self, code: str, code_verifier: str | None = None) -> TokenResult:
        raise NotImplementedError('Instagram publishing is not implemented yet. TODO: use Instagram Graph API Content Publishing.')

    async def refresh_token_if_needed(self, account: OAuthAccount) -> OAuthAccount:
        return account

    async def publish_text_link(self, account: OAuthAccount, payload: dict) -> str:
        raise NotImplementedError('Instagram stub connector. TODO: implement media container + publish flow.')

    async def get_follower_count(self, account: OAuthAccount) -> int | None:
        return None
