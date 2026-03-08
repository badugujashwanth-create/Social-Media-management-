import pytest
from app.connectors.x import XConnector
from app.crypto.token_vault import TokenVault
from app.models.oauth_account import OAuthAccount


class FakeResponse:
    def __init__(self, body):
        self._body = body
        self.status_code = 200

    def raise_for_status(self):
        return None

    def json(self):
        return self._body


class FakeClient:
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, json=None, headers=None, data=None, auth=None):
        assert url == 'https://api.x.com/2/tweets'
        assert 'Authorization' in headers
        assert 'text' in json
        return FakeResponse({'data': {'id': 'tweet_1'}})


@pytest.mark.asyncio
async def test_x_connector_publish(monkeypatch):
    import app.connectors.x as x_module

    monkeypatch.setattr(x_module.httpx, 'AsyncClient', lambda timeout=20: FakeClient())
    connector = XConnector()
    vault = TokenVault()
    account = OAuthAccount(
        user_id=1,
        platform='x',
        display_name='X',
        external_account_id='1',
        access_token_enc=vault.encrypt('raw-token'),
    )

    post_id = await connector.publish_text_link(account, {'text': 'hello', 'link_url': None})
    assert post_id == 'tweet_1'
