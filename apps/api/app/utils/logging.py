import logging
import uuid
from contextvars import ContextVar
from pythonjsonlogger.json import JsonFormatter
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

request_id_ctx: ContextVar[str] = ContextVar('request_id', default='')


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get('x-request-id') or str(uuid.uuid4())
        request_id_ctx.set(req_id)
        response = await call_next(request)
        response.headers['x-request-id'] = req_id
        return response


class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_ctx.get()
        return True


def configure_logging() -> None:
    handler = logging.StreamHandler()
    formatter = JsonFormatter('%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s')
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)
    root.addFilter(RequestIdFilter())
