from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from logseq_mcp.server import AppContext
from logseq_mcp.tools.core import health
from logseq_mcp.tools.write import block_append, block_delete, block_update
from tests.integration.conftest import SANDBOX_BASELINE_BLOCKS, find_block_by_content

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
