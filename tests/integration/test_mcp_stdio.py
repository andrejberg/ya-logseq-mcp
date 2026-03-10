from __future__ import annotations

import json

import pytest

from tests.integration.conftest import SANDBOX_BASELINE_BLOCKS, assert_protocol_clean_stdout, find_block_by_content

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


def _tool_payload(result):
    if result.structuredContent is not None:
        structured = result.structuredContent
        if isinstance(structured, dict) and "result" in structured:
            return json.loads(structured["result"])
        return structured

    texts = [item.text for item in result.content if hasattr(item, "text") and isinstance(item.text, str)]
    assert texts, f"tool returned no text content: {result!r}"
    assert len(texts) == 1, f"expected a single text payload, got {texts!r}"
    return json.loads(texts[0])


async def test_stdio_server_exposes_expected_tools(mcp_session):
    async with mcp_session as handle:
        result = await handle.session.list_tools()
        tool_names = {tool.name for tool in result.tools}

        missing = REQUIRED_TOOLS.difference(tool_names)
        assert not missing, f"missing tools {sorted(missing)} from stdio registry: {sorted(tool_names)}"
        assert_protocol_clean_stdout(handle.stderr_text)


async def test_mcp_health_and_get_page_round_trip(mcp_session, isolated_graph_env):
    async with mcp_session as handle:
        health_payload = _tool_payload(await handle.session.call_tool("health"))
        page_payload = _tool_payload(
            await handle.session.call_tool("get_page", {"name": isolated_graph_env.parity_page})
        )

        assert health_payload["status"] == "ok"
        assert health_payload["graph"] == isolated_graph_env.graph_name
        assert isinstance(health_payload["page_count"], int)

        assert page_payload["page"]["name"].lower() == isolated_graph_env.parity_page.lower()
        assert page_payload["block_count"] >= 1
        assert find_block_by_content(page_payload["blocks"], "Beta great-grandchild") is not None
        assert_protocol_clean_stdout(handle.stderr_text)


async def test_mcp_write_round_trip_uses_isolated_graph(
    live_client,
    seed_fixture_graph,
    mcp_session,
    isolated_graph_env,
):
    fixture_pages = await seed_fixture_graph(live_client)

    async with mcp_session as handle:
        health_payload = _tool_payload(await handle.session.call_tool("health"))
        assert health_payload["graph"] == isolated_graph_env.graph_name

        append_payload = _tool_payload(
            await handle.session.call_tool(
                "block_append",
                {
                    "page": fixture_pages["sandbox_page"],
                    "blocks": [
                        {
                            "content": "Phase 04 stdio sandbox root",
                            "children": [{"content": "Phase 04 stdio sandbox child"}],
                        }
                    ],
                },
            )
        )
        sandbox_root = find_block_by_content(append_payload["blocks"], "Phase 04 stdio sandbox root")
        assert append_payload["page"] == fixture_pages["sandbox_page"]
        assert append_payload["appended"] == 2
        assert sandbox_root is not None

        update_payload = _tool_payload(
            await handle.session.call_tool(
                "block_update",
                {"uuid": sandbox_root["uuid"], "content": "Phase 04 stdio sandbox root updated"},
            )
        )
        assert update_payload == {
            "uuid": sandbox_root["uuid"],
            "content": "Phase 04 stdio sandbox root updated",
        }

        delete_payload = _tool_payload(
            await handle.session.call_tool("block_delete", {"uuid": sandbox_root["uuid"]})
        )
        assert delete_payload == {"ok": True, "uuid": sandbox_root["uuid"]}

        readback_payload = _tool_payload(
            await handle.session.call_tool("get_page", {"name": fixture_pages["sandbox_page"]})
        )
        assert find_block_by_content(readback_payload["blocks"], "Phase 04 stdio sandbox root") is None
        assert find_block_by_content(readback_payload["blocks"], "Phase 04 stdio sandbox root updated") is None
        assert find_block_by_content(readback_payload["blocks"], "Phase 04 stdio sandbox child") is None
        for baseline in SANDBOX_BASELINE_BLOCKS:
            assert find_block_by_content(readback_payload["blocks"], baseline) is not None

        assert_protocol_clean_stdout(handle.stderr_text)


async def test_server_keeps_logs_off_stdout(mcp_session, isolated_graph_env):
    async with mcp_session as handle:
        await handle.session.call_tool("health")
        await handle.session.call_tool("get_page", {"name": isolated_graph_env.parity_page})

        stderr_text = handle.stderr_text
        assert "INFO" in stderr_text
        assert "health: checking Logseq connectivity" in stderr_text
        assert "get_page: fetching page" in stderr_text
        assert_protocol_clean_stdout(stderr_text)
