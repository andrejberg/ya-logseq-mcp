"""Failing test stubs for Phase 3 write tools — RED state.

Tests cover WRIT-01 through WRIT-05:
  WRIT-01: page_create creates a page with properties and optional initial blocks
  WRIT-02: block_append accepts flat strings and nested objects
  WRIT-03: block_append preserves hierarchy and ordering
  WRIT-04: block_update updates content and verifies readback
  WRIT-05: block_delete removes a block and verifies absence

All tests import their tools inside the test body so pytest can still
collect the file before write tool implementation is complete.
"""

import json
from unittest.mock import AsyncMock

import pytest
from mcp import McpError


@pytest.fixture
def token_env(monkeypatch):
    monkeypatch.setenv("LOGSEQ_API_TOKEN", "test-token")


def _make_ctx(mock_client=None):
    from logseq_mcp.server import AppContext

    client = mock_client or AsyncMock()
    mock_ctx = AsyncMock()
    mock_ctx.request_context.lifespan_context = AppContext(client=client)
    return mock_ctx


def _flatten_block_values(blocks: list[dict], field: str) -> list[str]:
    values: list[str] = []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        if field in block:
            values.append(block[field])
        children = block.get("children", [])
        if children:
            values.extend(_flatten_block_values(children, field))
    return values


async def test_page_create_with_properties_and_initial_blocks(token_env):
    from logseq_mcp.tools.write import page_create

    page_name = "Project Alpha"
    page_properties = {"type": "Project", "status": "active"}
    initial_blocks = [
        "root 1",
        {"content": "root 2", "properties": {"kind": "task"}, "children": [{"content": "child"}]},
    ]

    calls = []

    async def fake_call(method, *args):
        calls.append((method, args))
        if method == "logseq.Editor.createPage":
            return {"uuid": "page-uuid", "name": page_name}
        if method == "logseq.Editor.appendBlockInPage":
            content = args[1]
            if content == "root 1":
                return {"uuid": "root-1"}
            if content == "root 2":
                return {"uuid": "root-2"}
        if method == "logseq.Editor.insertBlock":
            return {"uuid": "child-1"}
        if method == "logseq.Editor.getPage":
            return {
                "id": 1,
                "uuid": "page-uuid",
                "name": page_name,
                "original-name": page_name,
                "properties": page_properties,
            }
        if method == "logseq.Editor.getPageBlocksTree":
            return [
                {"id": 10, "uuid": "root-1", "content": "root 1", "children": []},
                {
                    "id": 11,
                    "uuid": "root-2",
                    "content": "root 2",
                    "properties": {"kind": "task"},
                    "children": [{"id": 12, "uuid": "child-1", "content": "child", "children": []}],
                },
            ]
        return None

    client = AsyncMock()
    client._call = fake_call
    mock_ctx = _make_ctx(client)

    result = await page_create(
        mock_ctx,
        name=page_name,
        properties=page_properties,
        blocks=initial_blocks,
    )
    data = json.loads(result)

    assert calls[0] == (
        "logseq.Editor.createPage",
        (page_name, page_properties, {"createFirstBlock": False}),
    )
    assert [method for method, _ in calls[1:4]] == [
        "logseq.Editor.appendBlockInPage",
        "logseq.Editor.appendBlockInPage",
        "logseq.Editor.insertBlock",
    ]
    assert data["page"]["properties"] == page_properties
    assert _flatten_block_values(data["blocks"], "content") == ["root 1", "root 2", "child"]


async def test_block_append_accepts_strings_and_nested_objects(token_env):
    from logseq_mcp.tools.write import block_append

    payload = [
        "root 1",
        {"content": "root 2", "properties": {"kind": "task"}, "children": [{"content": "child"}]},
    ]
    calls = []

    async def fake_call(method, *args):
        calls.append((method, args))
        if method == "logseq.Editor.getPage":
            return {"id": 1, "uuid": "page-uuid", "name": "Project Alpha", "original-name": "Project Alpha"}
        if method == "logseq.Editor.appendBlockInPage":
            content = args[1]
            return {"uuid": "uuid-root-1" if content == "root 1" else "uuid-root-2"}
        if method == "logseq.Editor.insertBlock":
            return {"uuid": "uuid-child-1"}
        if method == "logseq.Editor.getPageBlocksTree":
            return [
                {"id": 10, "uuid": "uuid-root-1", "content": "root 1", "children": []},
                {
                    "id": 11,
                    "uuid": "uuid-root-2",
                    "content": "root 2",
                    "properties": {"kind": "task"},
                    "children": [{"id": 12, "uuid": "uuid-child-1", "content": "child", "children": []}],
                },
            ]
        return None

    client = AsyncMock()
    client._call = fake_call
    mock_ctx = _make_ctx(client)

    result = await block_append(mock_ctx, page="Project Alpha", blocks=payload)
    data = json.loads(result)

    append_calls = [call for call in calls if call[0] == "logseq.Editor.appendBlockInPage"]
    assert len(append_calls) == 2
    assert append_calls[0][1][1] == "root 1"
    assert append_calls[1][1][1] == "root 2"
    assert append_calls[1][1][2]["properties"] == {"kind": "task"}
    assert data["page"] == "Project Alpha"
    assert data["appended"] == 3
    assert data["block_count"] == 3
    insert_calls = [call for call in calls if call[0] == "logseq.Editor.insertBlock"]
    assert len(insert_calls) == 1
    assert insert_calls[0][1][0] == "uuid-root-2"
    assert insert_calls[0][1][1] == "child"
    assert insert_calls[0][1][2] == {"sibling": False}
    assert _flatten_block_values(data["blocks"], "content") == ["root 1", "root 2", "child"]


async def test_block_append_preserves_requested_hierarchy_and_order(token_env):
    from logseq_mcp.tools.write import block_append

    payload = [
        {"content": "parent a", "children": [{"content": "child a1"}, {"content": "child a2"}]},
        "parent b",
    ]
    calls = []

    async def fake_call(method, *args):
        calls.append((method, args))
        if method == "logseq.Editor.getPage":
            return {"id": 1, "uuid": "page-uuid", "name": "Project Alpha", "original-name": "Project Alpha"}
        if method == "logseq.Editor.appendBlockInPage":
            content = args[1]
            return {
                "uuid": {
                    "parent a": "uuid-parent-a",
                    "parent b": "uuid-parent-b",
                }[content]
            }
        if method == "logseq.Editor.insertBlock":
            content = args[1]
            return {
                "uuid": {
                    "child a1": "uuid-child-a1",
                    "child a2": "uuid-child-a2",
                }[content]
            }
        if method == "logseq.Editor.getPageBlocksTree":
            return [
                {
                    "id": 10,
                    "uuid": "uuid-parent-a",
                    "content": "parent a",
                    "children": [
                        {"id": 11, "uuid": "uuid-child-a1", "content": "child a1", "children": []},
                        {"id": 12, "uuid": "uuid-child-a2", "content": "child a2", "children": []},
                    ],
                },
                {"id": 13, "uuid": "uuid-parent-b", "content": "parent b", "children": []},
            ]
        return None

    client = AsyncMock()
    client._call = fake_call
    mock_ctx = _make_ctx(client)

    result = await block_append(mock_ctx, page="Project Alpha", blocks=payload)
    data = json.loads(result)

    assert [method for method, _ in calls[1:5]] == [
        "logseq.Editor.appendBlockInPage",
        "logseq.Editor.insertBlock",
        "logseq.Editor.insertBlock",
        "logseq.Editor.appendBlockInPage",
    ]
    assert calls[2][1][0] == "uuid-parent-a"
    assert calls[3][1][0] == "uuid-parent-a"
    assert calls[2][1][2] == {"sibling": False}
    assert calls[3][1][2] == {"sibling": False}
    assert data["appended"] == 4
    assert data["block_count"] == 4
    assert [block["content"] for block in data["blocks"]] == ["parent a", "parent b"]
    assert [child["content"] for child in data["blocks"][0]["children"]] == ["child a1", "child a2"]


async def test_block_update_changes_content_and_verifies_readback(token_env):
    from logseq_mcp.tools.write import block_update

    calls = []

    async def fake_call(method, *args):
        calls.append((method, args))
        if method == "logseq.Editor.getBlock":
            if len(calls) == 1:
                return {"id": 9, "uuid": "block-uuid", "content": "old content", "children": []}
            return {"id": 9, "uuid": "block-uuid", "content": "new content", "children": []}
        if method == "logseq.Editor.updateBlock":
            return {"uuid": "block-uuid"}
        return None

    client = AsyncMock()
    client._call = fake_call
    mock_ctx = _make_ctx(client)

    result = await block_update(mock_ctx, uuid="block-uuid", content="new content")
    data = json.loads(result)

    assert [method for method, _ in calls] == [
        "logseq.Editor.getBlock",
        "logseq.Editor.updateBlock",
        "logseq.Editor.getBlock",
    ]
    assert data["uuid"] == "block-uuid"
    assert data["content"] == "new content"


async def test_block_delete_removes_block_from_followup_reads(token_env):
    from logseq_mcp.tools.write import block_delete

    calls = []

    async def fake_call(method, *args):
        calls.append((method, args))
        if method == "logseq.Editor.getBlock":
            if len(calls) == 1:
                return {
                    "id": 9,
                    "uuid": "block-uuid",
                    "content": "to delete",
                    "page": {"id": 2, "uuid": "page-uuid", "name": "Project Alpha"},
                    "children": [],
                }
            return None
        if method == "logseq.Editor.removeBlock":
            return True
        if method == "logseq.Editor.getPageBlocksTree":
            return [
                {
                    "id": 11,
                    "uuid": "sibling-uuid",
                    "content": "sibling block",
                    "children": [],
                }
            ]
        return None

    client = AsyncMock()
    client._call = fake_call
    mock_ctx = _make_ctx(client)

    result = await block_delete(mock_ctx, uuid="block-uuid")
    data = json.loads(result)

    assert [method for method, _ in calls] == [
        "logseq.Editor.getBlock",
        "logseq.Editor.removeBlock",
        "logseq.Editor.getBlock",
        "logseq.Editor.getPageBlocksTree",
    ]
    assert data == {"ok": True, "uuid": "block-uuid"}


async def test_block_update_unchanged_readback_raises_explicit_error(token_env):
    from logseq_mcp.tools.write import block_update

    async def fake_call(method, *args):
        if method == "logseq.Editor.getBlock":
            return {"id": 9, "uuid": "block-uuid", "content": "old content", "children": []}
        if method == "logseq.Editor.updateBlock":
            return {"uuid": "block-uuid"}
        return None

    client = AsyncMock()
    client._call = fake_call
    mock_ctx = _make_ctx(client)

    with pytest.raises(McpError, match="updated content did not match"):
        await block_update(mock_ctx, uuid="block-uuid", content="new content")


async def test_invalid_nested_payload_fails_before_first_write(token_env):
    from logseq_mcp.tools.write import block_append

    client = AsyncMock()
    mock_ctx = _make_ctx(client)

    with pytest.raises((McpError, ValueError, TypeError)):
        await block_append(
            mock_ctx,
            page="Project Alpha",
            blocks=[{"content": "root", "children": ["invalid-child"]}],
        )

    client._call.assert_not_called()


async def test_block_append_missing_page_raises_explicit_error(token_env):
    from logseq_mcp.tools.write import block_append

    client = AsyncMock()
    client._call = AsyncMock(return_value=None)
    mock_ctx = _make_ctx(client)

    with pytest.raises(McpError, match="page not found"):
        await block_append(mock_ctx, page="Missing Page", blocks=["root 1"])


async def test_block_update_missing_uuid_raises_explicit_error(token_env):
    from logseq_mcp.tools.write import block_update

    client = AsyncMock()
    client._call = AsyncMock(return_value=None)
    mock_ctx = _make_ctx(client)

    with pytest.raises(McpError, match="block not found"):
        await block_update(mock_ctx, uuid="missing-uuid", content="updated")


async def test_block_delete_missing_uuid_raises_explicit_error(token_env):
    from logseq_mcp.tools.write import block_delete

    client = AsyncMock()
    client._call = AsyncMock(return_value=None)
    mock_ctx = _make_ctx(client)

    with pytest.raises(McpError, match="block not found"):
        await block_delete(mock_ctx, uuid="missing-uuid")
