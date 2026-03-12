from __future__ import annotations

import json

import pytest

from tests.integration.conftest import (
    SANDBOX_BASELINE_BLOCKS,
    assert_protocol_clean_stdout,
    find_block_by_content,
    launch_stdio_server,
)

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
    "journal_today",
    "journal_append",
    "journal_range",
    "move_block",
    "delete_page",
    "rename_page",
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


async def test_mcp_lifecycle_round_trip_uses_isolated_graph(
    live_client,
    seed_fixture_graph,
    lifecycle_page_factory,
    cleanup_lifecycle_page_fixture,
    mcp_session,
    isolated_graph_env,
):
    await seed_fixture_graph(live_client)
    source_name = lifecycle_page_factory("Stdio Rename Source", namespace="Phase 05 Namespace")
    target_name = lifecycle_page_factory("Stdio Rename Target", namespace="Phase 05 Namespace")

    try:
        async with mcp_session as handle:
            health_payload = _tool_payload(await handle.session.call_tool("health"))
            assert health_payload["graph"] == isolated_graph_env.graph_name

            create_payload = _tool_payload(
                await handle.session.call_tool(
                    "page_create",
                    {
                        "name": source_name,
                        "blocks": ["Phase 05 stdio lifecycle root"],
                    },
                )
            )
            assert create_payload["page"]["name"].casefold() == source_name.casefold()
            assert find_block_by_content(create_payload["blocks"], "Phase 05 stdio lifecycle root") is not None

            rename_payload = _tool_payload(
                await handle.session.call_tool(
                    "rename_page",
                    {"old_name": source_name, "new_name": target_name},
                )
            )
            assert rename_payload == {"ok": True, "old_name": source_name, "new_name": target_name}

            renamed_payload = _tool_payload(
                await handle.session.call_tool("get_page", {"name": target_name})
            )
            assert renamed_payload["page"]["name"].casefold() == target_name.casefold()
            assert find_block_by_content(renamed_payload["blocks"], "Phase 05 stdio lifecycle root") is not None

            delete_payload = _tool_payload(
                await handle.session.call_tool("delete_page", {"name": target_name})
            )
            assert delete_payload == {"ok": True, "name": target_name}

            missing_result = await handle.session.call_tool("get_page", {"name": target_name})
            error_texts = [item.text for item in missing_result.content if hasattr(item, "text")]
            assert error_texts, f"missing-page call returned no error text: {missing_result!r}"
            assert any("page not found" in text for text in error_texts)
            assert_protocol_clean_stdout(handle.stderr_text)
    finally:
        await cleanup_lifecycle_page_fixture(live_client, source_name)
        await cleanup_lifecycle_page_fixture(live_client, target_name)


async def test_mcp_move_block_round_trip_uses_isolated_graph(
    live_client,
    ensure_move_page_fixture,
    move_page_factory,
    cleanup_lifecycle_page_fixture,
    mcp_session,
    isolated_graph_env,
):
    page_name = move_page_factory("Stdio Move")

    try:
        fixture = await ensure_move_page_fixture(live_client, page_name)

        async with mcp_session as handle:
            health_payload = _tool_payload(await handle.session.call_tool("health"))
            assert health_payload["graph"] == isolated_graph_env.graph_name

            move_payload = _tool_payload(
                await handle.session.call_tool(
                    "move_block",
                    {
                        "uuid": fixture["source_uuid"],
                        "target_uuid": fixture["anchor_a_uuid"],
                        "position": "before",
                    },
                )
            )
            assert move_payload == {
                "ok": True,
                "uuid": fixture["source_uuid"],
                "target_uuid": fixture["anchor_a_uuid"],
                "position": "before",
            }

            page_payload = _tool_payload(await handle.session.call_tool("get_page", {"name": page_name}))
            top_level = page_payload["blocks"]
            ordered_uuids = [block["uuid"] for block in top_level]
            assert ordered_uuids.index(fixture["source_uuid"]) < ordered_uuids.index(fixture["anchor_a_uuid"])

            moved_root = find_block_by_content(page_payload["blocks"], "Move source")
            assert moved_root is not None
            assert find_block_by_content([moved_root], "Move source child") is not None
            assert find_block_by_content([moved_root], "Move source grandchild") is not None
            assert_protocol_clean_stdout(handle.stderr_text)
    finally:
        await cleanup_lifecycle_page_fixture(live_client, page_name)


async def test_mcp_move_block_cross_page_round_trip_uses_isolated_graph(
    live_client,
    ensure_cross_page_move_fixture,
    move_page_factory,
    cleanup_lifecycle_page_fixture,
    mcp_session,
    isolated_graph_env,
):
    source_page_name = move_page_factory("Stdio Cross Page Source")
    destination_page_name = move_page_factory("Stdio Cross Page Destination")

    try:
        fixture = await ensure_cross_page_move_fixture(live_client, source_page_name, destination_page_name)

        async with mcp_session as handle:
            health_payload = _tool_payload(await handle.session.call_tool("health"))
            assert health_payload["graph"] == isolated_graph_env.graph_name

            move_payload = _tool_payload(
                await handle.session.call_tool(
                    "move_block",
                    {
                        "uuid": fixture["source_uuid"],
                        "target_uuid": fixture["destination_anchor_uuid"],
                        "position": "after",
                    },
                )
            )
            assert move_payload == {
                "ok": True,
                "uuid": fixture["source_uuid"],
                "target_uuid": fixture["destination_anchor_uuid"],
                "position": "after",
            }

            destination_payload = _tool_payload(await handle.session.call_tool("get_page", {"name": destination_page_name}))
            source_payload = _tool_payload(await handle.session.call_tool("get_page", {"name": source_page_name}))
            destination_top_level = destination_payload["blocks"]
            ordered_uuids = [block["uuid"] for block in destination_top_level]
            assert ordered_uuids.index(fixture["source_uuid"]) > ordered_uuids.index(fixture["destination_anchor_uuid"])

            moved_root = find_block_by_content(destination_payload["blocks"], "Cross-page move source")
            assert moved_root is not None
            assert find_block_by_content([moved_root], "Cross-page move child") is not None
            assert find_block_by_content([moved_root], "Cross-page move grandchild") is not None
            assert find_block_by_content(source_payload["blocks"], "Cross-page move source") is None
            assert_protocol_clean_stdout(handle.stderr_text)
    finally:
        await cleanup_lifecycle_page_fixture(live_client, source_page_name)
        await cleanup_lifecycle_page_fixture(live_client, destination_page_name)


async def test_mcp_journal_today_round_trip_uses_isolated_graph(
    live_client,
    journal_page_factory,
    cleanup_journal_page_fixture,
    isolated_graph_env,
    monkeypatch,
):
    page_name = journal_page_factory()
    monkeypatch.setenv("LOGSEQ_MCP_TEST_TODAY", page_name)
    await cleanup_journal_page_fixture(live_client, page_name)

    try:
        async with launch_stdio_server(isolated_graph_env) as handle:
            health_payload = _tool_payload(await handle.session.call_tool("health"))
            assert health_payload["graph"] == isolated_graph_env.graph_name

            journal_payload = _tool_payload(await handle.session.call_tool("journal_today"))
            assert journal_payload["created"] is True
            assert journal_payload["page"]["name"] == page_name
            assert journal_payload["page"]["journal"] is True
            assert journal_payload["block_count"] == 0

            page_payload = _tool_payload(await handle.session.call_tool("get_page", {"name": page_name}))
            assert page_payload["page"]["name"] == page_name
            assert page_payload["page"]["journal"] is True
            assert page_payload["block_count"] == 0
            assert_protocol_clean_stdout(handle.stderr_text)
    finally:
        await cleanup_journal_page_fixture(live_client, page_name)


async def test_mcp_journal_append_round_trip_uses_isolated_graph(
    live_client,
    journal_append_date_factory,
    cleanup_journal_page_fixture,
    isolated_graph_env,
):
    page_name = journal_append_date_factory(32)
    await cleanup_journal_page_fixture(live_client, page_name)

    try:
        async with launch_stdio_server(isolated_graph_env) as handle:
            health_payload = _tool_payload(await handle.session.call_tool("health"))
            assert health_payload["graph"] == isolated_graph_env.graph_name

            journal_payload = _tool_payload(
                await handle.session.call_tool(
                    "journal_append",
                    {
                        "date": page_name,
                        "blocks": [
                            {
                                "content": "Phase 06 stdio journal root",
                                "children": [
                                    {
                                        "content": "Phase 06 stdio journal child",
                                        "children": [{"content": "Phase 06 stdio journal grandchild"}],
                                    }
                                ],
                            }
                        ],
                    },
                )
            )

            assert journal_payload["page"] == page_name
            assert journal_payload["appended"] == 3
            assert journal_payload["block_count"] == 3

            page_payload = _tool_payload(await handle.session.call_tool("get_page", {"name": page_name}))
            assert page_payload["page"]["name"] == page_name
            assert page_payload["page"]["journal"] is True

            root = find_block_by_content(page_payload["blocks"], "Phase 06 stdio journal root")
            assert root is not None
            child = find_block_by_content(root.get("children", []), "Phase 06 stdio journal child")
            assert child is not None
            assert find_block_by_content(child.get("children", []), "Phase 06 stdio journal grandchild") is not None
            assert_protocol_clean_stdout(handle.stderr_text)
    finally:
        await cleanup_journal_page_fixture(live_client, page_name)


async def test_mcp_journal_range_round_trip_uses_isolated_graph(
    live_client,
    journal_append_date_factory,
    cleanup_journal_page_fixture,
    isolated_graph_env,
):
    # Use two far-future disposable dates for the range window.
    start_page = journal_append_date_factory(400)
    end_page = journal_append_date_factory(401)
    await cleanup_journal_page_fixture(live_client, start_page)
    await cleanup_journal_page_fixture(live_client, end_page)

    try:
        async with launch_stdio_server(isolated_graph_env) as handle:
            health_payload = _tool_payload(await handle.session.call_tool("health"))
            assert health_payload["graph"] == isolated_graph_env.graph_name

            # Seed both journal pages with content via MCP transport.
            await handle.session.call_tool(
                "journal_append",
                {"date": start_page, "blocks": ["Phase 07 range start block"]},
            )
            await handle.session.call_tool(
                "journal_append",
                {"date": end_page, "blocks": ["Phase 07 range end block"]},
            )

            # Retrieve the inclusive range through MCP transport.
            range_payload = _tool_payload(
                await handle.session.call_tool(
                    "journal_range",
                    {"start_date": start_page, "end_date": end_page},
                )
            )
            assert range_payload["start_date"] == start_page
            assert range_payload["end_date"] == end_page
            assert range_payload["days"] == 2
            assert range_payload["entry_count"] == 2

            entry_dates = [e["page"]["name"] for e in range_payload["entries"]]
            assert start_page in entry_dates
            assert end_page in entry_dates

            start_entry = next(e for e in range_payload["entries"] if e["page"]["name"] == start_page)
            end_entry = next(e for e in range_payload["entries"] if e["page"]["name"] == end_page)
            assert find_block_by_content(start_entry["blocks"], "Phase 07 range start block") is not None
            assert find_block_by_content(end_entry["blocks"], "Phase 07 range end block") is not None

            assert_protocol_clean_stdout(handle.stderr_text)
    finally:
        await cleanup_journal_page_fixture(live_client, start_page)
        await cleanup_journal_page_fixture(live_client, end_page)


async def test_mcp_journal_range_reversed_fails_through_transport(
    isolated_graph_env,
    journal_append_date_factory,
):
    # Reversed range: end before start must surface an explicit McpError.
    start_page = journal_append_date_factory(402)
    end_page = journal_append_date_factory(403)

    async with launch_stdio_server(isolated_graph_env) as handle:
        result = await handle.session.call_tool(
            "journal_range",
            {"start_date": end_page, "end_date": start_page},
        )
        error_texts = [item.text for item in result.content if hasattr(item, "text")]
        assert error_texts, f"reversed range returned no error text: {result!r}"
        assert any("start_date must be on or before end_date" in text for text in error_texts)
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
