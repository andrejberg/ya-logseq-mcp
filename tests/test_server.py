"""Unit test stubs for MCP server + lifespan (FOUN-05, FOUN-06, FOUN-08).

These tests will be fully implemented in plan 03 when server.py exists.
"""

import pytest

pytest.importorskip("logseq_mcp.server", reason="server not yet implemented")


@pytest.mark.xfail(reason="server not yet implemented", strict=False)
def test_tool_registered(): ...


@pytest.mark.xfail(reason="server not yet implemented", strict=False)
def test_stderr_only(): ...


@pytest.mark.xfail(reason="server not yet implemented", strict=False)
def test_lifespan_closes_client(): ...
