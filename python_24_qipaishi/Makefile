.PHONY: install dev smoke test lint format migrate revision docker-up docker-down

CONDA_ENV ?= anti-spoofing_scc_175
PYTHON ?= conda run -n $(CONDA_ENV) python
UVICORN ?= conda run -n $(CONDA_ENV) uvicorn

install:
	python -m pip install -e ".[dev]"

dev:
	$(UVICORN) app.main:app --reload --host 0.0.0.0 --port 8000

smoke:
	$(PYTHON) scripts/smoke_api.py

test:
	pytest

lint:
	ruff check app tests

format:
	ruff format app tests

migrate:
	alembic upgrade head

revision:
	alembic revision --autogenerate -m "$(message)"

docker-up:
	docker compose up --build

docker-down:
	docker compose down
