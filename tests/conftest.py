"""Shared fixtures for pytest."""

import pytest


@pytest.fixture
def anyio_backend() -> str:
    """Configures the anyio backend for async tests."""
    return "asyncio"
