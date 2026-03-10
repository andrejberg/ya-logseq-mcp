from __future__ import annotations

import pytest

from tests.integration.conftest import assert_protocol_clean_stdout

pytestmark = [pytest.mark.asyncio, pytest.mark.integration]

REQUIRED_TOOLS = {
    "health",
    "get_page",
    "get_block",
    "list_pages",
    "get_references",
    "page_create",
    "block_append",
    "block_update",
    "block_delete",
}


async def test_stdio_server_exposes_expected_tools(mcp_session):
    async with mcp_session as handle:
        result = await handle.session.list_tools()
        tool_names = {tool.name for tool in result.tools}

        missing = REQUIRED_TOOLS.difference(tool_names)
        assert not missing, f"missing tools {sorted(missing)} from stdio registry: {sorted(tool_names)}"
        assert_protocol_clean_stdout(handle.stderr_text)
