.PHONY: infra migrate api worker web

infra:
	docker compose -f infra/docker-compose.yml up -d

migrate:
	cd apps/api && alembic upgrade head

api:
	cd apps/api && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

worker:
	cd apps/api && rq worker -u redis://localhost:6379/0 publish snapshot

web:
	cd apps/web && npm run dev
