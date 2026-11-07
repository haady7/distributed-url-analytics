.PHONY: up down logs test lint migrate shell load

up:
	cp -n .env.example .env || true
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f api worker

migrate:
	docker compose run --rm migrate

test:
	pytest

lint:
	ruff check app tests scripts

load:
	locust -f locustfile.py --host http://localhost:8000
