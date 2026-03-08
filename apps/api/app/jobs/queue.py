from redis import Redis
from rq import Queue
from app.config import get_settings

settings = get_settings()
redis_conn = Redis.from_url(settings.redis_url)
publish_queue = Queue('publish', connection=redis_conn)
snapshot_queue = Queue('snapshot', connection=redis_conn)
