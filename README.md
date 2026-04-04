# Social Media Control Center (SMCC)

SMCC is a monorepo MVP that connects social accounts, provides a unified dashboard, and publishes a single post to multiple platforms through official APIs only.

## Monorepo Structure

```
/smcc
  /apps
    /web        # Next.js 14 App Router frontend
    /api        # FastAPI backend + RQ worker
  /packages
    /shared     # shared platform/status constants (TS + Python)
  /infra
    docker-compose.yml
```

## Architecture Overview

- Frontend: Next.js 14 + TypeScript + Tailwind + shadcn-style components
- Backend: FastAPI + SQLAlchemy 2.0 + Alembic
- Database: PostgreSQL
- Queue: Redis + RQ
- Object storage: MinIO (S3-compatible local dev)
- Auth: email/password + JWT
- OAuth token storage: encrypted at rest with Fernet via `TOKEN_ENCRYPTION_KEY`
- Observability: structured JSON logs + request IDs

## MVP Features

- Sign up / login
- Connect accounts via OAuth (Facebook Pages, LinkedIn, X)
- Instagram connector scaffold (stub + TODO)
- Developer mode token paste endpoint (`POST /api/v1/accounts/dev`)
- Compose post (text + optional link + optional image upload)
- One-click publish to selected accounts or Post to All
- Per-target status: `queued | publishing | success | failed | rate_limited | needs_reauth`
- Retry handling for transient failures with exponential backoff via RQ retries
- Unified dashboard and posts history
- Analytics:
  - daily post counts
  - follower snapshot deltas
  - unfollower availability by connector (official API only)

## Environment Variables

Copy templates:

- `apps/api/.env.example` -> `apps/api/.env`
- `apps/web/.env.example` -> `apps/web/.env.local`
- Optional unified backend key: `AYRSHARE_API_KEY` in `apps/api/.env`

Generate Fernet key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Never commit real production secrets. The values in `apps/api/.env.example` are placeholders only.

## Run Locally

1. Start infra:
```bash
cd smcc/infra
docker compose up -d
```

2. Set `TOKEN_ENCRYPTION_KEY`:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

PowerShell example:
```powershell
$env:TOKEN_ENCRYPTION_KEY="<paste-generated-key>"
```

3. Run database migrations:
```bash
cd smcc/apps/api
alembic upgrade head
```

4. Start API on `:8000` (bind all interfaces in dev):
```bash
cd smcc/apps/api
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

5. Start RQ worker:
```bash
cd smcc/apps/api
rq worker -u redis://localhost:6379/0 publish snapshot
```

6. Start web on `:3000`:
```bash
cd smcc/apps/web
npm install
npm run dev -- --port 3000
```

- API: http://localhost:8000
- Web: http://localhost:3000

## Tests

```bash
cd apps/api
pytest
```

Included tests:
- token encryption/decryption
- publish job state transitions
- connector publish (X) with mocked client

## Deploy On Render

API web service:

- Branch: `main`
- Root Directory: `apps/api`
- Build Command: `pip install -r requirements.txt`
- Pre-Deploy Command: `alembic upgrade head`
- Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health Check Path: `/health`

Required API environment variables:

- `SECRET_KEY`
- `TOKEN_ENCRYPTION_KEY`
- `POSTGRES_DSN`
- `REDIS_URL`
- `APP_PUBLIC_URL`
- `API_PUBLIC_URL`
- `FRONTEND_BASE_URL`

Generate the Fernet key used by `TOKEN_ENCRYPTION_KEY`:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Notes:

- Render does not load your local `apps/api/.env`, so you must set the variables above in the Render dashboard.
- `TOKEN_ENCRYPTION_KEY` is required at application startup. If it is missing, the deploy will boot-fail before serving traffic.
- If you use Render Postgres, set `POSTGRES_DSN` with the SQLAlchemy driver prefix:
  `postgresql+psycopg2://...`
- Set `APP_PUBLIC_URL` and `FRONTEND_BASE_URL` to your frontend URL.
- Set `API_PUBLIC_URL` to `https://social-media-management-api.onrender.com`.

Additional services:

- Background worker:
  - Root Directory: `apps/api`
  - Build Command: `pip install -r requirements.txt`
  - Start Command: `rq worker -u $REDIS_URL publish snapshot`
- Postgres database
- Redis / Key Value service

Optional variables:

- S3 / object storage for uploads:
  - `S3_ENDPOINT`
  - `S3_ACCESS_KEY`
  - `S3_SECRET_KEY`
  - `S3_BUCKET`
  - `S3_REGION`
  - `S3_PUBLIC_BASE`
- OAuth providers:
  - `FACEBOOK_CLIENT_ID`
  - `FACEBOOK_CLIENT_SECRET`
  - `FACEBOOK_REDIRECT_URI`
  - `LINKEDIN_CLIENT_ID`
  - `LINKEDIN_CLIENT_SECRET`
  - `LINKEDIN_REDIRECT_URI`
  - `X_CLIENT_ID`
  - `X_CLIENT_SECRET`
  - `X_REDIRECT_URI`

## Using vendor repos

SMCC vendor references live under `vendor/`:

- `vendor/postiz-app`
- `vendor/django-social-scheduler`
- `vendor/socialmediascheduler`
- `vendor/ayrshare-js`
- `vendor/ayrshare-python`

Clone with submodules:

```bash
git clone --recurse-submodules <your-smcc-repo-url>
cd smcc
git submodule update --init --recursive
```

Bootstrap and update helpers:

```bash
./scripts/vendor_setup.sh
```

```powershell
.\scripts\vendor_setup.ps1
```

Warning on Postiz AGPL:

- `postiz-app` is AGPL-3.0.
- Do not copy Postiz code into SMCC unless SMCC is intentionally AGPL-compliant.
- Safe options: use as reference, or run Postiz as a separate service via API.

## Real OAuth Setup

- Meta (Facebook Pages):
  - Create a Meta app in Meta for Developers and add Facebook Login.
  - Add `https://social-media-management-api.onrender.com/oauth/facebook/callback` as a valid OAuth redirect URI.
  - Request permissions for Pages posting (`pages_manage_posts`, `pages_read_engagement`, `pages_show_list`).
  - Put `FACEBOOK_CLIENT_ID` and `FACEBOOK_CLIENT_SECRET` in `apps/api/.env`.
- LinkedIn:
  - Create an app in LinkedIn Developer Portal.
  - Add `https://social-media-management-api.onrender.com/oauth/linkedin/callback` as an authorized redirect URL.
  - Enable products/scopes needed for member posting (`w_member_social`, plus OpenID profile scopes).
  - Put `LINKEDIN_CLIENT_ID` and `LINKEDIN_CLIENT_SECRET` in `apps/api/.env`.
- X:
  - Create an app in X Developer Portal and enable OAuth 2.0.
  - Add `https://social-media-management-api.onrender.com/oauth/x/callback` as callback URL.
  - Enable scopes for posting and refresh tokens (`tweet.write`, `users.read`, `offline.access`).
  - Put `X_CLIENT_ID` and `X_CLIENT_SECRET` in `apps/api/.env`.

## Connector Plugin Contract

Connectors implement `app/connectors/base.py`:

- `platform_name`
- `capabilities() -> { supports_image, supports_link }`
- `is_enabled(settings)`
- `get_oauth_authorize_url(state, code_challenge=None)`
- `exchange_code_for_token(code, code_verifier=None)`
- `refresh_token_if_needed(account)`
- `publish_text_link(account, payload)`
- `get_follower_count(account)`
- optional `get_follower_list(account)`

Registry: `app/connectors/registry.py`

## How to Add a New Connector

1. Create `app/connectors/<platform>.py` implementing `Connector`.
2. Register it in `app/connectors/registry.py`.
3. Add platform env vars to `apps/api/.env.example`.
4. Add OAuth start/callback support (existing generic endpoints can be reused).
5. Add publish + follower count handling.
6. Expose platform option in `apps/web/app/accounts/page.tsx`.

## Limitations

- No scraping is used.
- "Who unfollowed" is only possible where official APIs provide follower lists.
- For most APIs in this MVP, follower tracking is snapshot delta only.
- OAuth details vary by app permissions and may require platform app review/setup.
- Instagram publishing is scaffolded only (stub connector).
- Image posting is disabled for Facebook, LinkedIn, and X in this MVP (text/link only).
