.PHONY: test backend-test frontend-test up down build health migrate seed lint docker-test validate-compose

test: backend-test frontend-test

backend-test:
	cd backend && (test -x .venv/Scripts/python.exe && .venv/Scripts/python.exe -m pytest -q || test -x .venv/bin/python && .venv/bin/python -m pytest -q || python -m pytest -q)

frontend-test:
	cd frontend && npm test

up:
	docker compose -f docker-compose.yml up --build -d

down:
	docker compose -f docker-compose.yml down

build:
	docker compose -f docker-compose.yml build

health:
	./scripts/docker-health.sh

migrate:
	docker compose -f docker-compose.yml exec -T backend alembic upgrade head

seed:
	cd backend && python -m app.seed

docker-test:
	./scripts/docker-test.sh

validate-compose:
	docker compose -f docker-compose.yml config >/dev/null
	docker compose -f docker-compose.yml -f docker-compose.dev.yml config >/dev/null

lint:
	cd backend && ruff check app tests || true
