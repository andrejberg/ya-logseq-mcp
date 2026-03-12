from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from typing import Any

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



@dataclass(frozen=True)
class NormalizedParityPage:
    name: str
    blocks: list[dict]
    block_count: int
    top_level_order: list[tuple[str | None, str | None]]
    uuid_counter: Counter[str]
    duplicate_map: dict[str, int]

    @property
    def duplicate_excess(self) -> int:
        return sum(count - 1 for count in self.duplicate_map.values())


def _decode_json_payload(candidate: Any) -> dict:
    if isinstance(candidate, dict):
        return candidate
    if isinstance(candidate, str):
        text = candidate.strip()
        if text:
            return json.loads(text)
    raise ValueError(f"unsupported JSON payload candidate: {candidate!r}")


def _tool_payload(result):
    if result.structuredContent is not None:
        structured = result.structuredContent
        if isinstance(structured, dict) and "result" in structured:
            try:
                return _decode_json_payload(structured["result"])
            except ValueError:
                pass
        if isinstance(structured, dict):
            return structured

    texts = [item.text for item in result.content if hasattr(item, "text") and isinstance(item.text, str)]
    assert texts, f"tool returned no text content: {result!r}"
    for text in texts:
        try:
            return _decode_json_payload(text)
        except (ValueError, json.JSONDecodeError):
            continue
    pytest.fail(f"tool returned no JSON payload: {texts!r}")


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


def _recursive_block_count(blocks: list[dict]) -> int:
    return sum(1 + _recursive_block_count(_block_children(block)) for block in blocks if isinstance(block, dict))


def _extract_block_count(payload: dict, blocks: list[dict]) -> int:
    for key in ("block_count", "blockCount"):
        value = payload.get(key)
        if isinstance(value, int):
            return value
    return _recursive_block_count(blocks)


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


def _normalize_parity_page(payload: dict, fixture_name: str) -> NormalizedParityPage:
    page = payload.get("page")
    if not isinstance(page, dict):
        pytest.fail("get_page payload missing page metadata")

    page_name = page.get("name")
    if not isinstance(page_name, str):
        pytest.fail("get_page payload missing a string page name")
    if page_name.lower() != fixture_name.lower():
        pytest.fail(f"Expected parity fixture name '{fixture_name}', got '{page_name}'")

    raw_blocks = payload.get("blocks")
    if not isinstance(raw_blocks, list):
        pytest.fail("get_page payload returned invalid blocks")

    normalized_blocks = _strip_fixture_title_block(raw_blocks, fixture_name)
    block_count = _extract_block_count(payload, normalized_blocks)
    uuid_counter = _uuid_counter(normalized_blocks)
    duplicate_map = _duplicate_uuids(normalized_blocks)

    return NormalizedParityPage(
        name=page_name,
        blocks=normalized_blocks,
        block_count=block_count,
        top_level_order=_top_level_order(normalized_blocks),
        uuid_counter=uuid_counter,
        duplicate_map=duplicate_map,
    )


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

    logseq_page = _normalize_parity_page(logseq_payload, isolated_graph_env.parity_page)
    graphthulhu_page = _normalize_parity_page(graphthulhu_payload, isolated_graph_env.parity_page)

    assert logseq_page.name.lower() == graphthulhu_page.name.lower()
    assert logseq_page.top_level_order == graphthulhu_page.top_level_order
    assert logseq_page.duplicate_map == {}, f"logseq-mcp returned duplicate UUIDs: {logseq_page.duplicate_map}"
    assert set(logseq_page.uuid_counter) == set(graphthulhu_page.uuid_counter)
    assert logseq_page.block_count <= graphthulhu_page.block_count

    if graphthulhu_page.block_count > logseq_page.block_count:
        block_excess = graphthulhu_page.block_count - logseq_page.block_count
        assert graphthulhu_page.duplicate_map, "graphthulhu block excess must be explainable as duplicate UUIDs"
        assert block_excess == graphthulhu_page.duplicate_excess


async def test_logseq_mcp_preserves_expected_child_nesting_on_parity_fixture(
    mcp_session,
    isolated_graph_env,
):
    async with mcp_session as handle:
        logseq_payload = _tool_payload(
            await handle.session.call_tool("get_page", {"name": isolated_graph_env.parity_page})
        )

    logseq_page = _normalize_parity_page(logseq_payload, isolated_graph_env.parity_page)
    assert _content_tree(logseq_page.blocks) == EXPECTED_PARITY_TREE
