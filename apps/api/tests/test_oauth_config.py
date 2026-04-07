from urllib.parse import parse_qs, urlparse

import pytest
from fastapi import HTTPException

from app.connectors.facebook import FacebookConnector
from app.connectors.linkedin import LinkedInConnector
from app.connectors.x import XConnector
from app.routes import oauth as oauth_routes


def _query_params(url: str) -> dict[str, list[str]]:
    return parse_qs(urlparse(url).query)


def test_oauth_authorize_urls_use_configured_redirects_and_scopes(monkeypatch):
    facebook = FacebookConnector()
    linkedin = LinkedInConnector()
    x = XConnector()

    monkeypatch.setattr(facebook.settings, 'facebook_client_id', 'facebook-client')
    monkeypatch.setattr(facebook.settings, 'facebook_redirect_uri', 'https://api.example.com/oauth/facebook/callback')
    monkeypatch.setattr(facebook.settings, 'facebook_oauth_scopes', 'pages_manage_posts,pages_show_list')

    monkeypatch.setattr(linkedin.settings, 'linkedin_client_id', 'linkedin-client')
    monkeypatch.setattr(linkedin.settings, 'linkedin_redirect_uri', 'https://api.example.com/oauth/linkedin/callback')
    monkeypatch.setattr(linkedin.settings, 'linkedin_oauth_scopes', 'openid profile w_member_social')

    monkeypatch.setattr(x.settings, 'x_client_id', 'x-client')
    monkeypatch.setattr(x.settings, 'x_redirect_uri', 'https://api.example.com/oauth/x/callback')
    monkeypatch.setattr(x.settings, 'x_oauth_scopes', 'tweet.write users.read offline.access')

    facebook_params = _query_params(facebook.get_oauth_authorize_url('state-facebook'))
    linkedin_params = _query_params(linkedin.get_oauth_authorize_url('state-linkedin'))
    x_params = _query_params(x.get_oauth_authorize_url('state-x', code_challenge='challenge'))

    assert facebook_params['redirect_uri'] == ['https://api.example.com/oauth/facebook/callback']
    assert facebook_params['scope'] == ['pages_manage_posts,pages_show_list']
    assert linkedin_params['redirect_uri'] == ['https://api.example.com/oauth/linkedin/callback']
    assert linkedin_params['scope'] == ['openid profile w_member_social']
    assert 'offline_access' not in linkedin_params['scope'][0]
    assert x_params['redirect_uri'] == ['https://api.example.com/oauth/x/callback']
    assert x_params['scope'] == ['tweet.write users.read offline.access']


def test_production_oauth_redirect_validation_rejects_localhost(monkeypatch):
    monkeypatch.setattr(oauth_routes.settings, 'environment', 'production')
    monkeypatch.setattr(oauth_routes.settings, 'api_public_url', 'https://api.example.com')
    monkeypatch.setattr(oauth_routes.settings, 'x_redirect_uri', 'http://localhost:8000/oauth/x/callback')

    with pytest.raises(HTTPException) as exc:
        oauth_routes._validate_oauth_redirect_uri('x')

    assert exc.value.status_code == 400
    assert 'redirect URI must be https://api.example.com/oauth/x/callback' in str(exc.value.detail)


def test_production_oauth_redirect_validation_accepts_deployed_callback(monkeypatch):
    monkeypatch.setattr(oauth_routes.settings, 'environment', 'production')
    monkeypatch.setattr(oauth_routes.settings, 'api_public_url', 'https://api.example.com')
    monkeypatch.setattr(oauth_routes.settings, 'x_redirect_uri', 'https://api.example.com/oauth/x/callback')

    oauth_routes._validate_oauth_redirect_uri('x')


@pytest.mark.asyncio
async def test_oauth_callback_provider_error_redirects_to_accounts(monkeypatch):
    monkeypatch.setattr(oauth_routes.settings, 'app_public_url', 'https://app.example.com')

    response = await oauth_routes.oauth_callback(
        platform='x',
        code=None,
        state=None,
        error='access_denied',
        error_description='User denied access',
    )

    assert response.status_code == 302
    location = response.headers['location']
    params = _query_params(location)
    assert location.startswith('https://app.example.com/accounts?')
    assert params['platform'] == ['x']
    assert params['oauth_error'] == ['User denied access']
