.PHONY: install dev test

install:
	uv sync

dev:
	uv run uvicorn src.main:app --reload --port 8000

test:
	uv run pytest
