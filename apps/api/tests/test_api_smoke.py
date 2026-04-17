from io import BytesIO

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base, get_db
from app.jobs import tasks
from app.main import app
from app.routes import posts as posts_routes
from app.routes import uploads as uploads_routes


class DummyQueue:
    def __init__(self):
        self.jobs: list[tuple[str, int, dict]] = []

    def enqueue(self, func, target_id, **kwargs):
        self.jobs.append((func.__name__, target_id, kwargs))
        return {'queued': True, 'target_id': target_id}


class FakeMinio:
    def __init__(self):
        self.bucket_created = False
        self.objects: dict[str, dict] = {}

    def bucket_exists(self, bucket):
        return self.bucket_created

    def make_bucket(self, bucket):
        self.bucket_created = True

    def put_object(self, bucket, key, data, length, content_type):
        self.objects[key] = {
            'bucket': bucket,
            'length': length,
            'content_type': content_type,
            'data': data.read(),
        }


def test_api_smoke_flow(tmp_path, monkeypatch):
    db_file = tmp_path / 'smoke.db'
    engine = create_engine(f'sqlite:///{db_file}')
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    dummy_queue = DummyQueue()
    fake_minio = FakeMinio()
    monkeypatch.setattr(posts_routes, 'publish_queue', dummy_queue)
    monkeypatch.setattr(tasks, 'SessionLocal', TestingSessionLocal)
    monkeypatch.setattr(uploads_routes, '_client', lambda: fake_minio)
    app.dependency_overrides[get_db] = override_get_db

    try:
        client = TestClient(app)

        signup = client.post('/api/v1/auth/signup', json={'email': 'smoke@example.com', 'password': 'pass1234'})
        assert signup.status_code == 200, signup.text
        token = signup.json()['access_token']
        headers = {'Authorization': f'Bearer {token}'}

        me = client.get('/api/v1/auth/me', headers=headers)
        assert me.status_code == 200, me.text

        accounts = client.get('/api/v1/accounts', headers=headers)
        assert accounts.status_code == 200, accounts.text
        assert accounts.json() == []

        account = client.post(
            '/api/v1/accounts/dev',
            headers=headers,
            json={
                'platform': 'x',
                'display_name': 'X Account',
                'external_account_id': 'x-1',
                'access_token': 'raw-token',
                'refresh_token': 'refresh-token',
                'scopes': 'tweet.write users.read offline.access',
            },
        )
        assert account.status_code == 200, account.text
        account_id = account.json()['id']

        post = client.post(
            '/api/v1/posts',
            headers=headers,
            json={
                'text': 'hello from smoke',
                'target_account_ids': [account_id],
                'post_to_all': False,
            },
        )
        assert post.status_code == 200, post.text
        assert len(dummy_queue.jobs) == 1

        posts = client.get('/api/v1/posts', headers=headers)
        assert posts.status_code == 200, posts.text
        assert len(posts.json()) == 1

        upload = client.post(
            '/api/v1/media/upload',
            headers=headers,
            files={'file': ('image.png', BytesIO(b'fakepng'), 'image/png')},
        )
        assert upload.status_code == 200, upload.text
        assert fake_minio.objects

        snapshot = client.post('/api/v1/analytics/snapshot', headers=headers)
        assert snapshot.status_code == 200, snapshot.text

        follower_deltas = client.get('/api/v1/analytics/follower-deltas', headers=headers)
        assert follower_deltas.status_code == 200, follower_deltas.text
        assert len(follower_deltas.json()) == 1

        availability = client.get('/api/v1/analytics/unfollowers-availability', headers=headers)
        assert availability.status_code == 200, availability.text

        dashboard = client.get('/api/v1/dashboard', headers=headers)
        assert dashboard.status_code == 200, dashboard.text

        health = client.get('/health')
        assert health.status_code == 200, health.text
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)
        engine.dispose()
