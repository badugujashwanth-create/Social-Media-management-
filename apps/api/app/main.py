from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from app.config import get_settings
from app.auth.security import decode_access_token
from app.utils.logging import configure_logging, RequestIDMiddleware
from app.routes import auth, accounts, posts, analytics, uploads, dashboard, oauth

settings = get_settings()
configure_logging()


def user_rate_limit_key(request: Request) -> str:
    auth_header = request.headers.get('authorization', '')
    if auth_header.lower().startswith('bearer '):
        token = auth_header.split(' ', 1)[1]
        try:
            payload = decode_access_token(token)
            return f"user:{payload.get('sub')}"
        except Exception:
            pass
    return f"ip:{get_remote_address(request)}"


limiter = Limiter(key_func=user_rate_limit_key, default_limits=[settings.app_rate_limit])
app = FastAPI(
    title='Social Media Control Center API',
    version='0.1.0',
    openapi_tags=[
        {'name': 'auth', 'description': 'Application authentication'},
        {'name': 'accounts', 'description': 'Connected social accounts and OAuth'},
        {'name': 'posts', 'description': 'Create and monitor cross-platform posts'},
        {'name': 'analytics', 'description': 'Posts and follower-change analytics'},
        {'name': 'uploads', 'description': 'Media uploads'},
        {'name': 'dashboard', 'description': 'Unified dashboard summary'},
    ],
)
app.state.limiter = limiter
app.add_middleware(RequestIDMiddleware)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_base_url, 'http://localhost:3000', 'http://127.0.0.1:3000'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(status_code=429, content={'detail': 'Rate limit exceeded'})


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={'detail': 'Internal server error'})


@app.get('/health')
def health():
    return {'status': 'ok'}


app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(accounts.router, prefix=settings.api_v1_prefix)
app.include_router(oauth.router, prefix=settings.api_v1_prefix)
app.include_router(oauth.router)
app.include_router(posts.router, prefix=settings.api_v1_prefix)
app.include_router(analytics.router, prefix=settings.api_v1_prefix)
app.include_router(uploads.router, prefix=settings.api_v1_prefix)
app.include_router(uploads.router)
app.include_router(dashboard.router, prefix=settings.api_v1_prefix)
