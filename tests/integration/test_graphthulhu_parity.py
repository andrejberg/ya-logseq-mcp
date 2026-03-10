from __future__ import annotations

import json
from collections import Counter

import pytest

pytestmark = [pytest.mark.asyncio, pytest.mark.integration]

EXPECTED_PARITY_TREE = [
    (
        "Alpha root",
        [
            ("Alpha child 1", [("Alpha grandchild 1", []), ("Alpha grandchild 2", [])]),
            ("Alpha child 2", []),
        ],
    ),
    (
        "Beta root",
        [
            ("Beta child", [("Beta grandchild", [("Beta great-grandchild", [])])]),
        ],
    ),
    (
        "Gamma root",
        [
            ("Gamma child 1", []),
            ("Gamma child 2", [("Gamma grandchild", [])]),
        ],
    ),
]


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


def _block_children(block: dict) -> list[dict]:
    children = block.get("children", [])
    return children if isinstance(children, list) else []


def _walk_blocks(blocks: list[dict]):
    for block in blocks:
        if not isinstance(block, dict):
            continue
        yield block
        yield from _walk_blocks(_block_children(block))


def _uuid_counter(blocks: list[dict]) -> Counter[str]:
    uuids = [
        uuid
        for uuid in (block.get("uuid") for block in _walk_blocks(blocks))
        if isinstance(uuid, str) and uuid
    ]
    return Counter(uuids)


def _duplicate_uuids(blocks: list[dict]) -> dict[str, int]:
    counts = _uuid_counter(blocks)
    return {uuid: count for uuid, count in counts.items() if count > 1}


def _duplicate_excess(blocks: list[dict]) -> int:
    return sum(count - 1 for count in _duplicate_uuids(blocks).values())


def _recursive_block_count(blocks: list[dict]) -> int:
    return sum(1 + _recursive_block_count(_block_children(block)) for block in blocks if isinstance(block, dict))


def _content_tree(blocks: list[dict]):
    return [
        (
            block.get("content"),
            _content_tree(_block_children(block)),
        )
        for block in blocks
        if isinstance(block, dict)
    ]


def _strip_fixture_title_block(blocks: list[dict], page_name: str) -> list[dict]:
    if not blocks:
        return blocks

    first = blocks[0]
    if not isinstance(first, dict):
        return blocks

    content = first.get("content")
    if isinstance(content, str) and content.strip().lower() == f"# {page_name}".lower():
        return blocks[1:]

    return blocks


def _top_level_order(blocks: list[dict]):
    return [
        (block.get("uuid"), block.get("content"))
        for block in blocks
        if isinstance(block, dict)
    ]


async def test_get_page_parity_fixture_has_fewer_duplicate_blocks_than_graphthulhu(
    mcp_session,
    graphthulhu_mcp_session,
    isolated_graph_env,
):
    async with mcp_session as logseq_handle, graphthulhu_mcp_session as graphthulhu_handle:
        logseq_payload = _tool_payload(
            await logseq_handle.session.call_tool("get_page", {"name": isolated_graph_env.parity_page})
        )
        graphthulhu_payload = _tool_payload(
            await graphthulhu_handle.session.call_tool("get_page", {"name": isolated_graph_env.parity_page})
        )

    logseq_blocks = logseq_payload["blocks"]
    graphthulhu_blocks = graphthulhu_payload["blocks"]

    assert logseq_payload["page"]["name"].lower() == isolated_graph_env.parity_page.lower()
    assert graphthulhu_payload["page"]["name"].lower() == isolated_graph_env.parity_page.lower()
    assert logseq_payload["page"]["name"].lower() == graphthulhu_payload["page"]["name"].lower()
    assert _top_level_order(logseq_blocks) == _top_level_order(graphthulhu_blocks)

    logseq_duplicates = _duplicate_uuids(logseq_blocks)
    graphthulhu_duplicates = _duplicate_uuids(graphthulhu_blocks)

    assert logseq_duplicates == {}, f"logseq-mcp returned duplicate UUIDs: {logseq_duplicates}"
    assert _recursive_block_count(logseq_blocks) == logseq_payload["block_count"]
    assert _recursive_block_count(graphthulhu_blocks) == graphthulhu_payload["blockCount"]

    logseq_uuid_set = set(_uuid_counter(logseq_blocks))
    graphthulhu_uuid_set = set(_uuid_counter(graphthulhu_blocks))
    assert logseq_uuid_set == graphthulhu_uuid_set

    logseq_count = logseq_payload["block_count"]
    graphthulhu_count = graphthulhu_payload["blockCount"]
    assert logseq_count <= graphthulhu_count

    if graphthulhu_count > logseq_count:
        excess = graphthulhu_count - logseq_count
        assert graphthulhu_duplicates, "graphthulhu block excess must be explainable as duplicate UUIDs"
        assert excess == _duplicate_excess(graphthulhu_blocks)


async def test_logseq_mcp_preserves_expected_child_nesting_on_parity_fixture(
    mcp_session,
    isolated_graph_env,
):
    async with mcp_session as handle:
        logseq_payload = _tool_payload(
            await handle.session.call_tool("get_page", {"name": isolated_graph_env.parity_page})
        )

    assert logseq_payload["page"]["name"].lower() == isolated_graph_env.parity_page.lower()
    assert _content_tree(
        _strip_fixture_title_block(logseq_payload["blocks"], isolated_graph_env.parity_page)
    ) == EXPECTED_PARITY_TREE
