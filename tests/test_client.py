"""Unit test stubs for LogseqClient (FOUN-01, FOUN-02, FOUN-03).

These tests will be fully implemented in plan 02 when client.py exists.
"""

import pytest

pytest.importorskip("logseq_mcp.client", reason="client not yet implemented")


# These will be filled in during plan 02 execution
@pytest.mark.xfail(reason="client not yet implemented", strict=False)
def test_auth_header(): ...


@pytest.mark.xfail(reason="client not yet implemented", strict=False)
def test_retry_on_transport_error(): ...


@pytest.mark.xfail(reason="client not yet implemented", strict=False)
def test_retry_on_5xx(): ...


@pytest.mark.xfail(reason="client not yet implemented", strict=False)
def test_no_retry_on_4xx(): ...


@pytest.mark.xfail(reason="client not yet implemented", strict=False)
def test_semaphore_serializes(): ...
