import base64
import pytest

import os

os.environ.setdefault('TOKEN_ENCRYPTION_KEY', base64.urlsafe_b64encode(b'12345678901234567890123456789012').decode())
os.environ.setdefault('SECRET_KEY', 'test-secret')
os.environ.setdefault('POSTGRES_DSN', 'sqlite:///:memory:')


@pytest.fixture(autouse=True)
def token_key_env(monkeypatch):
    key = base64.urlsafe_b64encode(b'12345678901234567890123456789012').decode()
    monkeypatch.setenv('TOKEN_ENCRYPTION_KEY', key)
    monkeypatch.setenv('SECRET_KEY', 'test-secret')
