from rq import Connection, Worker
from app.jobs.queue import redis_conn


if __name__ == '__main__':
    with Connection(redis_conn):
        worker = Worker(['publish', 'snapshot'])
        worker.work()
