.PHONY: test backend-test frontend-test up down migrate seed lint

test: backend-test frontend-test

backend-test:
	cd backend && (test -x .venv/Scripts/python.exe && .venv/Scripts/python.exe -m pytest -q || python -m pytest -q)

frontend-test:
	cd frontend && npm test

up:
	docker compose up --build

down:
	docker compose down

migrate:
	cd backend && alembic upgrade head

seed:
	cd backend && python -m app.seed

lint:
	cd backend && ruff check app tests || true
