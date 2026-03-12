from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from logseq_mcp.server import AppContext
from logseq_mcp.tools.core import health
from logseq_mcp.tools.write import (
    block_append,
    block_delete,
    block_update,
    delete_page,
    journal_append,
    journal_range,
    journal_today,
    move_block,
    rename_page,
)
from tests.integration.conftest import LIFECYCLE_PAGE_PREFIX, SANDBOX_BASELINE_BLOCKS, find_block_by_content

pytestmark = [pytest.mark.asyncio, pytest.mark.integration]


def _make_ctx(client) -> SimpleNamespace:
    return SimpleNamespace(
        request_context=SimpleNamespace(
            lifespan_context=AppContext(client=client),
        )
    )


def _find_top_level_index(blocks: list[dict], uuid: str) -> int:
    for index, block in enumerate(blocks):
        if block.get("uuid") == uuid:
            return index
    pytest.fail(f"Top-level block '{uuid}' not found in readback tree")


def _find_block_by_uuid(blocks: list[dict], uuid: str) -> dict | None:
    for block in blocks:
        if block.get("uuid") == uuid:
            return block
        children = block.get("children", [])
        if isinstance(children, list):
            nested = _find_block_by_uuid(children, uuid)
            if nested is not None:
                return nested
    return None


async def test_health_requires_isolated_graph(
    live_client,
    isolated_graph_env,
    assert_isolated_graph,
):
    graph_name = await assert_isolated_graph(live_client)

    payload = json.loads(await health(_make_ctx(live_client)))

    assert payload["status"] == "ok"
    assert payload["graph"] == isolated_graph_env.graph_name
    assert graph_name == isolated_graph_env.graph_name
    assert isinstance(payload["page_count"], int)


async def test_fixture_pages_are_present_before_mutation(
    live_client,
    isolated_graph_env,
    assert_isolated_graph,
    seed_fixture_graph,
):
    await assert_isolated_graph(live_client)

    parity_page = await live_client._call("logseq.Editor.getPage", isolated_graph_env.parity_page)
    sandbox_page = await live_client._call("logseq.Editor.getPage", isolated_graph_env.sandbox_page)

    if parity_page is None:
        pytest.fail(
            f"Parity fixture page '{isolated_graph_env.parity_page}' is missing from the isolated graph."
        )
    if sandbox_page is None:
        pytest.fail(
            f"Sandbox fixture page '{isolated_graph_env.sandbox_page}' is missing from the isolated graph."
        )

    fixture_pages = await seed_fixture_graph(live_client)
    parity_blocks = await live_client._call("logseq.Editor.getPageBlocksTree", fixture_pages["parity_page"])
    sandbox_blocks = await live_client._call("logseq.Editor.getPageBlocksTree", fixture_pages["sandbox_page"])

    assert isinstance(parity_blocks, list)
    assert isinstance(sandbox_blocks, list)
    assert find_block_by_content(parity_blocks, "Beta great-grandchild") is not None
    for baseline in SANDBOX_BASELINE_BLOCKS:
        assert find_block_by_content(sandbox_blocks, baseline) is not None


async def test_write_tools_use_sandbox_page_only(
    live_client,
    isolated_graph_env,
    assert_isolated_graph,
    seed_fixture_graph,
):
    await assert_isolated_graph(live_client)
    fixture_pages = await seed_fixture_graph(live_client)

    parity_before = await live_client._call("logseq.Editor.getPageBlocksTree", fixture_pages["parity_page"])
    appended = json.loads(
        await block_append(
            _make_ctx(live_client),
            fixture_pages["sandbox_page"],
            [
                {
                    "content": "Phase 04 sandbox root",
                    "children": [{"content": "Phase 04 sandbox child"}],
                }
            ],
        )
    )

    assert appended["page"] == isolated_graph_env.sandbox_page
    assert appended["appended"] == 2

    sandbox_root = find_block_by_content(appended["blocks"], "Phase 04 sandbox root")
    sandbox_child = find_block_by_content(appended["blocks"], "Phase 04 sandbox child")
    assert sandbox_root is not None
    assert sandbox_child is not None

    updated = json.loads(
        await block_update(
            _make_ctx(live_client),
            sandbox_root["uuid"],
            "Phase 04 sandbox root updated",
        )
    )
    assert updated == {
        "uuid": sandbox_root["uuid"],
        "content": "Phase 04 sandbox root updated",
    }

    deleted = json.loads(await block_delete(_make_ctx(live_client), sandbox_root["uuid"]))
    assert deleted == {"ok": True, "uuid": sandbox_root["uuid"]}

    sandbox_after = await live_client._call("logseq.Editor.getPageBlocksTree", fixture_pages["sandbox_page"])
    parity_after = await live_client._call("logseq.Editor.getPageBlocksTree", fixture_pages["parity_page"])

    assert isinstance(sandbox_after, list)
    assert find_block_by_content(sandbox_after, "Phase 04 sandbox root") is None
    assert find_block_by_content(sandbox_after, "Phase 04 sandbox root updated") is None
    assert find_block_by_content(sandbox_after, "Phase 04 sandbox child") is None
    for baseline in SANDBOX_BASELINE_BLOCKS:
        assert find_block_by_content(sandbox_after, baseline) is not None

    assert parity_after == parity_before


async def test_delete_page_uses_disposable_target(
    live_client,
    isolated_graph_env,
    assert_isolated_graph,
    seed_fixture_graph,
    lifecycle_page_factory,
    ensure_lifecycle_page_fixture,
    cleanup_lifecycle_page_fixture,
):
    await assert_isolated_graph(live_client)
    fixture_pages = await seed_fixture_graph(live_client)
    page_name = lifecycle_page_factory("Delete Target")

    try:
        assert page_name not in {fixture_pages["parity_page"], fixture_pages["sandbox_page"]}
        assert page_name.startswith(LIFECYCLE_PAGE_PREFIX)

        await ensure_lifecycle_page_fixture(
            live_client,
            page_name,
            ["Phase 05 lifecycle delete root"],
        )
        assert await live_client._call("logseq.Editor.getPage", page_name) is not None

        payload = json.loads(await delete_page(_make_ctx(live_client), page_name))

        assert payload == {"ok": True, "name": page_name}
        assert await live_client._call("logseq.Editor.getPage", page_name) is None
        assert await live_client._call("logseq.Editor.getPage", fixture_pages["parity_page"]) is not None
        assert await live_client._call("logseq.Editor.getPage", fixture_pages["sandbox_page"]) is not None
    finally:
        await cleanup_lifecycle_page_fixture(live_client, page_name)


async def test_rename_page_uses_disposable_target(
    live_client,
    isolated_graph_env,
    assert_isolated_graph,
    seed_fixture_graph,
    lifecycle_page_factory,
    ensure_lifecycle_page_fixture,
    cleanup_lifecycle_page_fixture,
):
    await assert_isolated_graph(live_client)
    fixture_pages = await seed_fixture_graph(live_client)
    source_name = lifecycle_page_factory("Rename Source")
    target_name = lifecycle_page_factory("Rename Target")

    try:
        assert source_name not in {fixture_pages["parity_page"], fixture_pages["sandbox_page"]}
        assert target_name not in {fixture_pages["parity_page"], fixture_pages["sandbox_page"]}
        assert source_name != target_name
        assert await live_client._call("logseq.Editor.getPage", target_name) is None

        await ensure_lifecycle_page_fixture(
            live_client,
            source_name,
            ["Phase 05 lifecycle rename root"],
        )

        payload = json.loads(await rename_page(_make_ctx(live_client), source_name, target_name))

        assert payload == {"ok": True, "old_name": source_name, "new_name": target_name}
        assert await live_client._call("logseq.Editor.getPage", source_name) is None
        renamed = await live_client._call("logseq.Editor.getPage", target_name)
        assert isinstance(renamed, dict)
        assert isinstance(renamed.get("name"), str)
        assert renamed["name"].casefold() == target_name.casefold()
        if isinstance(renamed.get("original-name"), str):
            assert renamed["original-name"] == target_name
    finally:
        await cleanup_lifecycle_page_fixture(live_client, source_name)
        await cleanup_lifecycle_page_fixture(live_client, target_name)


async def test_namespaced_lifecycle_pages_round_trip(
    live_client,
    assert_isolated_graph,
    lifecycle_page_factory,
    ensure_lifecycle_page_fixture,
    cleanup_lifecycle_page_fixture,
):
    await assert_isolated_graph(live_client)
    source_name = lifecycle_page_factory("Namespaced Source", namespace="Phase 05 Namespace")
    target_name = lifecycle_page_factory("Namespaced Target", namespace="Phase 05 Namespace")

    try:
        page = await ensure_lifecycle_page_fixture(
            live_client,
            source_name,
            ["Phase 05 lifecycle namespace root"],
        )
        payload = json.loads(await rename_page(_make_ctx(live_client), source_name, target_name))
        resolved = await live_client._call("logseq.Editor.getPage", target_name)

        assert isinstance(page.get("name"), str)
        assert page["name"].casefold() == source_name.casefold()
        if isinstance(page.get("original-name"), str):
            assert page["original-name"] == source_name
        assert payload == {"ok": True, "old_name": source_name, "new_name": target_name}
        assert await live_client._call("logseq.Editor.getPage", source_name) is None
        assert isinstance(resolved, dict)
        assert isinstance(resolved.get("name"), str)
        assert resolved["name"].casefold() == target_name.casefold()
        if isinstance(resolved.get("original-name"), str):
            assert resolved["original-name"] == target_name

        deleted = json.loads(await delete_page(_make_ctx(live_client), target_name))
        assert deleted == {"ok": True, "name": target_name}
        assert await live_client._call("logseq.Editor.getPage", target_name) is None
    finally:
        await cleanup_lifecycle_page_fixture(live_client, source_name)
        await cleanup_lifecycle_page_fixture(live_client, target_name)


async def test_move_block_before_preserves_subtree(
    live_client,
    assert_isolated_graph,
    move_page_factory,
    ensure_move_page_fixture,
    cleanup_lifecycle_page_fixture,
):
    await assert_isolated_graph(live_client)
    page_name = move_page_factory("Before")

    try:
        fixture = await ensure_move_page_fixture(live_client, page_name)

        payload = json.loads(
            await move_block(
                _make_ctx(live_client),
                fixture["source_uuid"],
                fixture["anchor_a_uuid"],
                "before",
            )
        )
        page_blocks = await live_client._call("logseq.Editor.getPageBlocksTree", page_name)

        assert payload == {
            "ok": True,
            "uuid": fixture["source_uuid"],
            "target_uuid": fixture["anchor_a_uuid"],
            "position": "before",
        }
        assert _find_top_level_index(page_blocks, fixture["source_uuid"]) < _find_top_level_index(
            page_blocks, fixture["anchor_a_uuid"]
        )
        moved = _find_block_by_uuid(page_blocks, fixture["source_uuid"])
        assert moved is not None
        assert _find_block_by_uuid([moved], fixture["source_child_uuid"]) is not None
        assert _find_block_by_uuid([moved], fixture["source_grandchild_uuid"]) is not None
    finally:
        await cleanup_lifecycle_page_fixture(live_client, page_name)


async def test_move_block_after_preserves_subtree(
    live_client,
    assert_isolated_graph,
    move_page_factory,
    ensure_move_page_fixture,
    cleanup_lifecycle_page_fixture,
):
    await assert_isolated_graph(live_client)
    page_name = move_page_factory("After")

    try:
        fixture = await ensure_move_page_fixture(live_client, page_name)

        payload = json.loads(
            await move_block(
                _make_ctx(live_client),
                fixture["source_uuid"],
                fixture["anchor_b_uuid"],
                "after",
            )
        )
        page_blocks = await live_client._call("logseq.Editor.getPageBlocksTree", page_name)

        assert payload == {
            "ok": True,
            "uuid": fixture["source_uuid"],
            "target_uuid": fixture["anchor_b_uuid"],
            "position": "after",
        }
        assert _find_top_level_index(page_blocks, fixture["source_uuid"]) > _find_top_level_index(
            page_blocks, fixture["anchor_b_uuid"]
        )
        moved = _find_block_by_uuid(page_blocks, fixture["source_uuid"])
        assert moved is not None
        assert _find_block_by_uuid([moved], fixture["source_child_uuid"]) is not None
        assert _find_block_by_uuid([moved], fixture["source_grandchild_uuid"]) is not None
    finally:
        await cleanup_lifecycle_page_fixture(live_client, page_name)


async def test_move_block_child_preserves_subtree(
    live_client,
    assert_isolated_graph,
    move_page_factory,
    ensure_move_page_fixture,
    cleanup_lifecycle_page_fixture,
):
    await assert_isolated_graph(live_client)
    page_name = move_page_factory("Child")

    try:
        fixture = await ensure_move_page_fixture(live_client, page_name)

        payload = json.loads(
            await move_block(
                _make_ctx(live_client),
                fixture["source_uuid"],
                fixture["anchor_b_uuid"],
                "child",
            )
        )
        page_blocks = await live_client._call("logseq.Editor.getPageBlocksTree", page_name)

        assert payload == {
            "ok": True,
            "uuid": fixture["source_uuid"],
            "target_uuid": fixture["anchor_b_uuid"],
            "position": "child",
        }
        anchor_b = _find_block_by_uuid(page_blocks, fixture["anchor_b_uuid"])
        assert anchor_b is not None
        moved = _find_block_by_uuid(anchor_b.get("children", []), fixture["source_uuid"])
        assert moved is not None
        assert _find_block_by_uuid([moved], fixture["source_child_uuid"]) is not None
        assert _find_block_by_uuid([moved], fixture["source_grandchild_uuid"]) is not None
    finally:
        await cleanup_lifecycle_page_fixture(live_client, page_name)


async def test_move_block_cross_page_preserves_subtree_on_destination_page(
    live_client,
    assert_isolated_graph,
    move_page_factory,
    ensure_cross_page_move_fixture,
    cleanup_lifecycle_page_fixture,
):
    await assert_isolated_graph(live_client)
    source_page_name = move_page_factory("Cross Page Source")
    destination_page_name = move_page_factory("Cross Page Destination")

    try:
        fixture = await ensure_cross_page_move_fixture(live_client, source_page_name, destination_page_name)

        payload = json.loads(
            await move_block(
                _make_ctx(live_client),
                fixture["source_uuid"],
                fixture["destination_anchor_uuid"],
                "after",
            )
        )
        destination_blocks = await live_client._call("logseq.Editor.getPageBlocksTree", destination_page_name)
        source_blocks = await live_client._call("logseq.Editor.getPageBlocksTree", source_page_name)

        assert payload == {
            "ok": True,
            "uuid": fixture["source_uuid"],
            "target_uuid": fixture["destination_anchor_uuid"],
            "position": "after",
        }
        assert _find_top_level_index(destination_blocks, fixture["source_uuid"]) > _find_top_level_index(
            destination_blocks, fixture["destination_anchor_uuid"]
        )
        moved = _find_block_by_uuid(destination_blocks, fixture["source_uuid"])
        assert moved is not None
        assert _find_block_by_uuid([moved], fixture["source_child_uuid"]) is not None
        assert _find_block_by_uuid([moved], fixture["source_grandchild_uuid"]) is not None
        assert _find_block_by_uuid(source_blocks, fixture["source_uuid"]) is None
    finally:
        await cleanup_lifecycle_page_fixture(live_client, source_page_name)
        await cleanup_lifecycle_page_fixture(live_client, destination_page_name)


async def test_journal_today_creates_missing_journal_page(
    live_client,
    assert_isolated_graph,
    journal_page_factory,
    cleanup_journal_page_fixture,
    monkeypatch,
):
    await assert_isolated_graph(live_client)
    page_name = journal_page_factory()
    monkeypatch.setenv("LOGSEQ_MCP_TEST_TODAY", page_name)

    await cleanup_journal_page_fixture(live_client, page_name)

    try:
        payload = json.loads(await journal_today(_make_ctx(live_client)))
        readback_page = await live_client._call("logseq.Editor.getPage", page_name)

        assert payload["created"] is True
        assert payload["page"]["name"] == page_name
        assert payload["page"]["journal"] is True
        assert payload["block_count"] == 0
        assert payload["blocks"] == []
        assert isinstance(readback_page, dict)
        assert readback_page.get("name") == page_name
        assert readback_page.get("journal?") is True
    finally:
        await cleanup_journal_page_fixture(live_client, page_name)


async def test_journal_append_preserves_nested_blocks_for_date(
    live_client,
    assert_isolated_graph,
    journal_append_date_factory,
    cleanup_journal_page_fixture,
):
    await assert_isolated_graph(live_client)
    page_name = journal_append_date_factory(31)
    await cleanup_journal_page_fixture(live_client, page_name)

    try:
        payload = json.loads(
            await journal_append(
                _make_ctx(live_client),
                date=page_name,
                blocks=[
                    {
                        "content": "Phase 06 journal root",
                        "children": [
                            {
                                "content": "Phase 06 journal child",
                                "children": [{"content": "Phase 06 journal grandchild"}],
                            }
                        ],
                    }
                ],
            )
        )
        readback_page = await live_client._call("logseq.Editor.getPage", page_name)
        readback_blocks = await live_client._call("logseq.Editor.getPageBlocksTree", page_name)

        assert payload["page"] == page_name
        assert payload["appended"] == 3
        assert payload["block_count"] == 3
        assert isinstance(readback_page, dict)
        assert readback_page.get("name") == page_name
        assert readback_page.get("journal?") is True
        assert isinstance(readback_blocks, list)

        root = find_block_by_content(payload["blocks"], "Phase 06 journal root")
        assert root is not None
        child = find_block_by_content(root.get("children", []), "Phase 06 journal child")
        assert child is not None
        grandchild = find_block_by_content(child.get("children", []), "Phase 06 journal grandchild")
        assert grandchild is not None

        readback_root = find_block_by_content(readback_blocks, "Phase 06 journal root")
        assert readback_root is not None
        readback_child = find_block_by_content(readback_root.get("children", []), "Phase 06 journal child")
        assert readback_child is not None
        assert find_block_by_content(readback_child.get("children", []), "Phase 06 journal grandchild") is not None
    finally:
        await cleanup_journal_page_fixture(live_client, page_name)


async def test_journal_range_returns_inclusive_existing_entries_only(
    live_client,
    assert_isolated_graph,
    journal_append_date_factory,
    cleanup_journal_page_fixture,
):
    """Live: journal_range returns only existing journal pages in the requested inclusive window."""
    await assert_isolated_graph(live_client)

    # Use far-future offsets (+410/+411) to stay isolated from existing phase fixtures
    start_page = journal_append_date_factory(410)
    end_page = journal_append_date_factory(411)

    # +411 day is inside the range; +409 day is outside (not seeded, not returned)
    await cleanup_journal_page_fixture(live_client, start_page)
    await cleanup_journal_page_fixture(live_client, end_page)

    try:
        # Seed start_page only — end_page intentionally absent to verify sparse skip
        await journal_append(
            _make_ctx(live_client),
            date=start_page,
            blocks=[{"content": "Phase 07 range start block"}],
        )

        result = json.loads(
            await journal_range(_make_ctx(live_client), start_date=start_page, end_date=end_page)
        )

        assert result["start_date"] == start_page
        assert result["end_date"] == end_page
        assert result["days"] == 2
        # Only start_page seeded — end_page absent so entry_count must be 1
        assert result["entry_count"] == 1
        assert len(result["entries"]) == 1

        entry = result["entries"][0]
        assert entry["page"]["name"] == start_page
        assert entry["page"]["journal"] is True
        assert entry["block_count"] >= 1
        assert find_block_by_content(entry["blocks"], "Phase 07 range start block") is not None
    finally:
        await cleanup_journal_page_fixture(live_client, start_page)
        await cleanup_journal_page_fixture(live_client, end_page)


async def test_journal_range_reversed_range_fails_on_live_graph(
    live_client,
    assert_isolated_graph,
    journal_append_date_factory,
):
    """Live: reversed start/end dates raise an explicit McpError before any Logseq API call."""
    from mcp import McpError

    await assert_isolated_graph(live_client)

    # Use far-future offsets (+412/+413) for the reversed-range test
    later_page = journal_append_date_factory(413)
    earlier_page = journal_append_date_factory(412)

    # McpError fires before any getPage call, so no live_client seeding needed
    with pytest.raises(McpError) as exc_info:
        await journal_range(_make_ctx(live_client), start_date=later_page, end_date=earlier_page)

    assert "start_date must be on or before end_date" in exc_info.value.error.message
