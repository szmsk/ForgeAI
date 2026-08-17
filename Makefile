.PHONY: up down test lint backend-check build scan

up:
	docker compose up --build

down:
	docker compose down

test:
	cd backend && pytest -q

lint:
	cd backend && ruff check app tests

backend-check:
	cd backend && python -m compileall -q app

build:
	docker compose build

scan:
	python scripts/secret_scan.py
