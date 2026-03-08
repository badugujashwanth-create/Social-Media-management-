# Third-Party Repositories and License Rules

## Critical Rule: Postiz (AGPL)

Postiz is licensed under AGPL-3.0. For SMCC this means:

- We MUST NOT copy Postiz source code into SMCC unless we intentionally make SMCC AGPL-compliant.
- Allowed:
  - Use Postiz as inspiration and architecture reference.
  - Run Postiz as a separate service and integrate through API boundaries.
  - Re-license SMCC under AGPL if we decide to incorporate AGPL code directly.

## Repository License Summary

| Repo | Intended Path | License | Usage Rule in SMCC |
|---|---|---|---|
| `gitroomhq/postiz-app` | `vendor/postiz-app` | AGPL-3.0 | Reference-only unless SMCC adopts AGPL obligations. |
| `ClimenteA/social-media-posts-scheduler` | `vendor/django-social-scheduler` | MIT | Safe to borrow patterns and code with attribution + copyright notice retention. |
| `Masterjx9/socialmediascheduler` | `vendor/socialmediascheduler` | README says MIT (license file should be verified at pinned commit) | Treat as reference until license artifact is confirmed in pinned vendor snapshot. |
| `ayrshare/social-media-api` | `vendor/ayrshare-js` | MIT (declared in `package.json`) | Prefer API-level integration; if copying snippets, keep MIT notice text with distributed copies. |
| `ayrshare/social-post-api-python` | `vendor/ayrshare-python` | Apache-2.0 (declared in `setup.py`) | API usage is simplest; if code is copied, preserve Apache notices and include required attribution. |

## Practical Compliance Rules for This Repo

- Keep all vendor code isolated under `vendor/`.
- Do not copy code from AGPL sources into `apps/` or `packages/` unless legal and licensing decision is explicit.
- Track pinned commit hashes for each submodule in release notes.
- Re-check license file presence when bumping vendor references.
- If unsure, prefer API-level integration over code copying.
