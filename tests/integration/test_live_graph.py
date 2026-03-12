from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from logseq_mcp.server import AppContext
from logseq_mcp.tools.core import health
from logseq_mcp.tools.write import block_append, block_delete, block_update, delete_page, rename_page
from tests.integration.conftest import LIFECYCLE_PAGE_PREFIX, SANDBOX_BASELINE_BLOCKS, find_block_by_content

pytestmark = [pytest.mark.asyncio, pytest.mark.integration]


def _make_ctx(client) -> SimpleNamespace:
    return SimpleNamespace(
        request_context=SimpleNamespace(
            lifespan_context=AppContext(client=client),
        )
    )


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
