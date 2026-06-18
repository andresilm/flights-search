.PHONY: install dev test check

install:
	uv sync

dev:
	uv run uvicorn src.app.main:app --reload --port 8000

test:
	uv run pytest

check:
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy src tests
	uv run pytest
