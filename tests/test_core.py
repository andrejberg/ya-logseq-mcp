"""Failing test stubs for Phase 2 core reads — RED state.

Tests cover READ-01 through READ-06:
  READ-01: get_page deduplicates blocks by UUID
  READ-02: get_page produces correct parent/child nesting
  READ-03: get_page calls API with page name, not UUID
  READ-04: get_block returns a single block by UUID
  READ-05: list_pages filters by namespace prefix
  READ-06: get_references parses linked-references response

All tests import their tools inside the test body so pytest can still
collect all tests even if one import fails.

pytest-asyncio asyncio_mode is "auto" in pyproject.toml — no decorator needed.
"""

import json
from unittest.mock import AsyncMock

import pytest


@pytest.fixture
def token_env(monkeypatch):
    monkeypatch.setenv("LOGSEQ_API_TOKEN", "test-token")


def _collect_uuids(blocks: list) -> list[str]:
    """Recursively walk a list of block dicts and return all uuid values found."""
    uuids = []
    for block in blocks:
        if isinstance(block, dict):
            if "uuid" in block:
                uuids.append(block["uuid"])
            children = block.get("children", [])
            if children:
                uuids.extend(_collect_uuids(children))
    return uuids


# ---------------------------------------------------------------------------
# Helpers to build mock context
# ---------------------------------------------------------------------------

def _make_ctx(fake_call):
    """Return an AsyncMock context with the given _call coroutine attached."""
    from logseq_mcp.server import AppContext

    mock_client = AsyncMock()
    mock_client._call = fake_call

    mock_ctx = AsyncMock()
    mock_ctx.request_context.lifespan_context = AppContext(client=mock_client)
    return mock_ctx


# ---------------------------------------------------------------------------
# READ-01: deduplication
# ---------------------------------------------------------------------------

async def test_get_page_no_duplicate_uuids(token_env):
    """get_page must not return the same UUID more than once (READ-01).

    Raw API returns block B at the top level AND as a child of block A —
    replicating the graphthulhu duplication bug. get_page must deduplicate.
    """
    from logseq_mcp.tools.core import get_page

    # Logseq getPage returns the page entity
    fake_page = {"id": 1, "uuid": "page-uuid", "name": "my-page", "original-name": "my-page"}

    # getPageBlocksTree returns B at top level AND nested under A
    fake_blocks = [
        {
            "id": 10,
            "uuid": "uuid-A",
            "content": "Block A",
            "children": [
                {"id": 20, "uuid": "uuid-B", "content": "Block B", "children": []}
            ],
        },
        # B also appears at top level — the duplication bug
        {"id": 20, "uuid": "uuid-B", "content": "Block B", "children": []},
    ]

    async def fake_call(method, *args):
        if method == "logseq.Editor.getPage":
            return fake_page
        if method == "logseq.Editor.getPageBlocksTree":
            return fake_blocks
        return None

    mock_ctx = _make_ctx(fake_call)
    result = await get_page(mock_ctx, "my-page")
    data = json.loads(result)

    all_uuids = _collect_uuids(data["blocks"])
    assert len(all_uuids) == len(set(all_uuids)), (
        f"Duplicate UUIDs found: {all_uuids}"
    )


# ---------------------------------------------------------------------------
# READ-02: nesting
# ---------------------------------------------------------------------------

async def test_get_page_nesting_correct(token_env):
    """get_page must return B nested under A, not at the top level (READ-02)."""
    from logseq_mcp.tools.core import get_page

    fake_page = {"id": 1, "uuid": "page-uuid", "name": "my-page", "original-name": "my-page"}

    # Same duplication scenario as READ-01
    fake_blocks = [
        {
            "id": 10,
            "uuid": "uuid-A",
            "content": "Block A",
            "children": [
                {"id": 20, "uuid": "uuid-B", "content": "Block B", "children": []}
            ],
        },
        {"id": 20, "uuid": "uuid-B", "content": "Block B", "children": []},
    ]

    async def fake_call(method, *args):
        if method == "logseq.Editor.getPage":
            return fake_page
        if method == "logseq.Editor.getPageBlocksTree":
            return fake_blocks
        return None

    mock_ctx = _make_ctx(fake_call)
    result = await get_page(mock_ctx, "my-page")
    data = json.loads(result)

    top_level = data["blocks"]
    top_uuids = [b["uuid"] for b in top_level]

    # Only A at top level — B must NOT appear at top level
    assert len(top_level) == 1, f"Expected 1 top-level block, got {len(top_level)}: {top_uuids}"
    assert top_level[0]["uuid"] == "uuid-A"
    assert "uuid-B" not in top_uuids, "uuid-B must not appear at top level"

    # B must be nested under A
    children = top_level[0].get("children", [])
    child_uuids = [c["uuid"] for c in children]
    assert "uuid-B" in child_uuids, f"uuid-B missing from A's children: {child_uuids}"


# ---------------------------------------------------------------------------
# READ-03: API called with page name
# ---------------------------------------------------------------------------

async def test_get_page_uses_name(token_env):
    """get_page must call getPageBlocksTree with the page name string (READ-03)."""
    from logseq_mcp.tools.core import get_page

    fake_page = {
        "id": 1,
        "uuid": "page-uuid-xyz",
        "name": "my-page",
        "original-name": "my-page",
    }

    calls = []

    async def fake_call(method, *args):
        calls.append((method, args))
        if method == "logseq.Editor.getPage":
            return fake_page
        if method == "logseq.Editor.getPageBlocksTree":
            return []
        return None

    mock_ctx = _make_ctx(fake_call)
    await get_page(mock_ctx, "my-page")

    tree_calls = [(m, a) for m, a in calls if m == "logseq.Editor.getPageBlocksTree"]
    assert len(tree_calls) >= 1, "getPageBlocksTree was never called"

    first_arg = tree_calls[0][1][0]  # first positional arg
    assert first_arg == "my-page", (
        f"Expected getPageBlocksTree to be called with 'my-page', got {first_arg!r}"
    )


# ---------------------------------------------------------------------------
# READ-04: get_block
# ---------------------------------------------------------------------------

async def test_get_block_returns_block(token_env):
    """get_block must return the block dict with uuid and content (READ-04)."""
    from logseq_mcp.tools.core import get_block

    fake_block = {
        "id": 42,
        "uuid": "block-uuid",
        "content": "Hello",
        "children": [],
    }

    async def fake_call(method, *args):
        if method == "logseq.Editor.getBlock":
            return fake_block
        return None

    mock_ctx = _make_ctx(fake_call)
    result = await get_block(mock_ctx, "block-uuid")
    data = json.loads(result)

    assert data["uuid"] == "block-uuid"
    assert data["content"] == "Hello"


# ---------------------------------------------------------------------------
# READ-05: list_pages namespace filter
# ---------------------------------------------------------------------------

async def test_list_pages_namespace_filter(token_env):
    """list_pages(namespace='projects') must exclude pages outside that namespace (READ-05)."""
    from logseq_mcp.tools.core import list_pages

    fake_pages = [
        {"id": 1, "uuid": "u1", "name": "projects/alpha", "original-name": "projects/alpha"},
        {"id": 2, "uuid": "u2", "name": "projects/beta", "original-name": "projects/beta"},
        {"id": 3, "uuid": "u3", "name": "daily", "original-name": "daily"},
    ]

    async def fake_call(method, *args):
        if method == "logseq.Editor.getAllPages":
            return fake_pages
        return None

    mock_ctx = _make_ctx(fake_call)
    result = await list_pages(mock_ctx, namespace="projects")
    data = json.loads(result)

    assert len(data) == 2, f"Expected 2 pages, got {len(data)}: {[p['name'] for p in data]}"
    names = [p["name"] for p in data]
    assert "daily" not in names, "'daily' must be excluded when filtering by namespace 'projects'"
    assert all(n.startswith("projects/") for n in names), f"All names must start with 'projects/': {names}"


async def test_list_pages_tolerates_namespace_page_refs(token_env):
    """list_pages must not fail when Logseq returns namespace as a page ref object."""
    from logseq_mcp.tools.core import list_pages

    fake_pages = [
        {
            "id": 2390,
            "uuid": "u-namespace",
            "name": "hls__20240820_research_data_policy_sfb1552_v1/1_1760532126520_0",
            "original-name": "hls__20240820_research_data_policy_sfb1552_v1/1_1760532126520_0",
            "namespace": {"id": 2393},
        },
        {"id": 3, "uuid": "u3", "name": "daily", "original-name": "daily"},
    ]

    async def fake_call(method, *args):
        if method == "logseq.Editor.getAllPages":
            return fake_pages
        return None

    mock_ctx = _make_ctx(fake_call)
    result = await list_pages(mock_ctx, include_journals=True, limit=10)
    data = json.loads(result)

    assert [page["name"] for page in data] == [
        "daily",
        "hls__20240820_research_data_policy_sfb1552_v1/1_1760532126520_0",
    ]


# ---------------------------------------------------------------------------
# READ-06: get_references parses linked-references response
# ---------------------------------------------------------------------------

async def test_get_references_parses_response(token_env):
    """get_references must return list of {page, blocks} dicts (READ-06)."""
    from logseq_mcp.tools.core import get_references

    fake_page_dict = {"id": 5, "name": "source-page", "original-name": "source-page"}
    fake_block_dict = {
        "id": 99,
        "uuid": "ref-block-uuid",
        "content": "See [[target-page]]",
        "children": [],
    }

    # Logseq returns [[page_dict, [block_dict, ...]], ...]
    fake_refs = [[fake_page_dict, [fake_block_dict]]]

    async def fake_call(method, *args):
        if method == "logseq.Editor.getPageLinkedReferences":
            return fake_refs
        return None

    mock_ctx = _make_ctx(fake_call)
    result = await get_references(mock_ctx, "target-page")
    data = json.loads(result)

    assert len(data) == 1, f"Expected 1 reference entry, got {len(data)}"
    entry = data[0]
    assert "page" in entry, f"Entry missing 'page' key: {entry}"
    assert "blocks" in entry, f"Entry missing 'blocks' key: {entry}"
    assert len(entry["blocks"]) == 1
