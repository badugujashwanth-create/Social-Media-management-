# SMCC Vendor References

## Why we're using it

We are using these repositories to accelerate connector design, scheduler orchestration, and platform coverage decisions without copying third-party code blindly. The goal is to reuse architecture patterns, endpoint mappings, and operational playbooks while keeping SMCC's code and license boundary explicit.

## 1) Postiz (`vendor/postiz-app`)

- Repo: `https://github.com/gitroomhq/postiz-app`
- License: AGPL-3.0
- Tech stack:
  - Monorepo with PNPM workspaces
  - Next.js frontend
  - NestJS backend
  - Shared SDK and orchestration apps
- What to reuse:
  - Product and workflow ideas for scheduling, queues, and multi-network UX
  - API boundary patterns from `apps/backend/src`
  - Multi-service layout and shared package patterns
- What NOT to reuse:
  - Source code snippets, copied modules, or integrated AGPL internals in SMCC proprietary code
  - Any code path that would create derivative-work obligations unless SMCC is intentionally AGPL
- Key folders to read:
  - `apps/backend/src`
  - `apps/frontend/src`
  - `apps/sdk/src`
  - `apps/orchestrator`
  - `libraries/`

## 2) Django Social Scheduler (`vendor/django-social-scheduler`)

- Repo: `https://github.com/ClimenteA/social-media-posts-scheduler`
- License: MIT
- Tech stack:
  - Django app
  - Alpine.js templates
  - Dockerized services and background poster process
- What to reuse:
  - Practical OAuth callback + token storage flows
  - Scheduler and publish orchestration patterns in Django
  - Platform adapter layout and conventions
- What NOT to reuse:
  - Project-specific UI templates and branding
  - Hard-coded env assumptions or deployment defaults that do not match SMCC infra
- Key folders to read:
  - `integrations/platforms/`
  - `integrations/models.py`
  - `integrations/views.py`
  - `socialsched/schedule_utils.py`
  - `socialsched/models.py`

## 3) Master Scheduler (`vendor/socialmediascheduler`)

- Repo: `https://github.com/Masterjx9/socialmediascheduler`
- License: README states MIT (verify LICENSE file when pinning commit)
- Tech stack:
  - Python desktop scheduler
  - React Native mobile app
  - Multi-platform API helpers
- What to reuse:
  - Connector-specific request payload shapes
  - Scheduling UX ideas for per-platform jobs
  - Credential/config examples for quick local testing
- What NOT to reuse:
  - Desktop/mobile app scaffolding not aligned with SMCC web + FastAPI architecture
  - Embedded assumptions around ngrok/local desktop runtime
- Key folders to read:
  - `Desktop_version/apis/`
  - `Desktop_version/scheduler/`
  - `Desktop_version/controller/`
  - `Mobile_version/lib/`
  - `sample.env`

## 4) Ayrshare JS SDK (`vendor/ayrshare-js`)

- Repo: `https://github.com/ayrshare/social-media-api`
- License: MIT (`package.json`)
- Tech stack:
  - Node.js SDK wrapper over Ayrshare REST API
- What to reuse:
  - Endpoint mapping and payload conventions for `/api/post`, history, delete
  - Error handling behavior for API responses
  - Multi-platform post payload shape (`post`, `platforms`, `mediaUrls`)
- What NOT to reuse:
  - SDK internals when direct HTTP integration in Python is simpler
  - Client-side assumptions not needed by backend-only connector flow
- Key folders/files to read:
  - `index.js`
  - `index.cjs`
  - `test.js`
  - `README.md`

## 5) Ayrshare Python SDK (`vendor/ayrshare-python`)

- Repo: `https://github.com/ayrshare/social-post-api-python`
- License: Apache-2.0 (declared in `setup.py`; verify when pinning commit)
- Tech stack:
  - Python SDK wrapper over Ayrshare REST API
  - `requests`-based transport
- What to reuse:
  - Python request shape and header conventions for Ayrshare API
  - Convenience method mapping for post/history/delete
  - Reference behavior for connector fallback and key usage
- What NOT to reuse:
  - Full SDK import path when minimal direct `httpx` integration is enough
  - Outdated helper methods without contract validation for SMCC
- Key folders/files to read:
  - `ayrshare/ayrshare.py`
  - `ayrshare/__init__.py`
  - `smoke_test.py`
  - `README.md`
