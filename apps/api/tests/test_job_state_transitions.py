import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db import Base
from app.models.user import User
from app.models.oauth_account import OAuthAccount
from app.models.post import Post, PostTarget
from app.models.enums import PostTargetStatus
from app.crypto.token_vault import TokenVault
from app.jobs import tasks


class FakeConnector:
    def __init__(self, should_fail=False):
        self.should_fail = should_fail

    async def refresh_token_if_needed(self, account):
        return account

    async def publish_text_link(self, account, payload):
        if self.should_fail:
            raise Exception('429 rate limited')
        return 'ext_123'


def _setup_db():
    engine = create_engine('sqlite:///:memory:')
    TestingSessionLocal = sessionmaker(bind=engine)
    Base.metadata.create_all(engine)
    return TestingSessionLocal


def test_publish_task_success(monkeypatch):
    Session = _setup_db()
    monkeypatch.setattr(tasks, 'SessionLocal', Session)
    monkeypatch.setattr(tasks, 'get_connectors', lambda: {'x': FakeConnector()})

    db = Session()
    user = User(email='u@example.com', password_hash='x')
    db.add(user)
    db.flush()
    vault = TokenVault()
    acc = OAuthAccount(user_id=user.id, platform='x', display_name='x', external_account_id='1', access_token_enc=vault.encrypt('t'))
    db.add(acc)
    db.flush()
    post = Post(user_id=user.id, text='hello')
    db.add(post)
    db.flush()
    target = PostTarget(post_id=post.id, oauth_account_id=acc.id, platform='x', status=PostTargetStatus.queued)
    db.add(target)
    db.commit()
    target_id = target.id
    db.close()

    tasks.publish_task(target_id)

    db2 = Session()
    updated = db2.get(PostTarget, target_id)
    assert updated.status == PostTargetStatus.success
    assert updated.external_post_id == 'ext_123'


def test_publish_task_rate_limited_requeues(monkeypatch):
    Session = _setup_db()
    monkeypatch.setattr(tasks, 'SessionLocal', Session)
    monkeypatch.setattr(tasks, 'get_connectors', lambda: {'x': FakeConnector(should_fail=True)})

    db = Session()
    user = User(email='u2@example.com', password_hash='x')
    db.add(user)
    db.flush()
    vault = TokenVault()
    acc = OAuthAccount(user_id=user.id, platform='x', display_name='x', external_account_id='1', access_token_enc=vault.encrypt('t'))
    db.add(acc)
    db.flush()
    post = Post(user_id=user.id, text='hello')
    db.add(post)
    db.flush()
    target = PostTarget(post_id=post.id, oauth_account_id=acc.id, platform='x', status=PostTargetStatus.queued)
    db.add(target)
    db.commit()
    target_id = target.id
    db.close()

    with pytest.raises(Exception):
        tasks.publish_task(target_id)

    db2 = Session()
    updated = db2.get(PostTarget, target_id)
    assert updated.status == PostTargetStatus.queued
    assert updated.error_code == 'rate_limited'
