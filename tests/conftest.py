"""Shared pytest fixtures for logseq-mcp tests."""

import pytest
import httpx


@pytest.fixture
def logseq_200():
    """Return a callable that creates a 200 JSON response with a given result."""

    def _make(result: object = None) -> httpx.Response:
        return httpx.Response(200, json={"result": result or {}})

    return _make


@pytest.fixture
def mock_transport(logseq_200):
    """Return an httpx.MockTransport that always responds with a 200 JSON response."""

    def handler(request: httpx.Request) -> httpx.Response:
        return logseq_200()

    return httpx.MockTransport(handler)
