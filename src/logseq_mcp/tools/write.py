import json
import logging

from mcp import McpError
from mcp.server.fastmcp import Context
from mcp.types import ErrorData, INTERNAL_ERROR
from pydantic import BaseModel, Field, ValidationError, model_validator

from logseq_mcp.server import AppContext, mcp
from logseq_mcp.types import BlockEntity, PageEntity

logger = logging.getLogger(__name__)


class WriteBlockInput(BaseModel):
    content: str
    properties: dict = Field(default_factory=dict)
    children: list["WriteBlockInput"] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def validate_node(cls, value):
        if not isinstance(value, dict):
            raise TypeError("block payload must be an object")

        content = value.get("content")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("block content must be a non-empty string")

        properties = value.get("properties", {})
        if properties is None:
            properties = {}
        if not isinstance(properties, dict):
            raise TypeError("block properties must be a dict")

        children = value.get("children", [])
        if children is None:
            children = []
        if not isinstance(children, list):
            raise TypeError("block children must be a list")
        for child in children:
            if not isinstance(child, dict):
                raise TypeError("nested block children must be objects")

        normalized = dict(value)
        normalized["content"] = content
        normalized["properties"] = properties
        normalized["children"] = children
        return normalized


WriteBlockInput.model_rebuild()


def _count_blocks(blocks: list[BlockEntity]) -> int:
    total = 0
    for block in blocks:
        total += 1 + _count_blocks(block.children)
    return total


def _parse_block_tree(raw_blocks: list) -> list[BlockEntity]:
    parsed: list[BlockEntity] = []
    for raw in raw_blocks:
        parsed.append(BlockEntity.model_validate(raw))
    return parsed


def _contains_block_uuid(blocks: list[BlockEntity], uuid: str) -> bool:
    for block in blocks:
        if block.uuid == uuid or _contains_block_uuid(block.children, uuid):
            return True
    return False


def _normalize_blocks(blocks: None | str | dict | list) -> list[WriteBlockInput]:
    if blocks is None:
        return []

    raw_nodes = blocks if isinstance(blocks, list) else [blocks]
    normalized: list[WriteBlockInput] = []

    for raw_node in raw_nodes:
        if isinstance(raw_node, str):
            normalized.append(WriteBlockInput(content=raw_node))
            continue

        if not isinstance(raw_node, dict):
            raise TypeError("blocks must be strings, objects, or lists of them")

        normalized.append(WriteBlockInput.model_validate(raw_node))

    return normalized


def _mutation_options(block: WriteBlockInput, *, child: bool = False) -> dict:
    opts: dict = {}
    if child:
        opts["sibling"] = False
    if block.properties:
        opts["properties"] = block.properties
    return opts


def _extract_uuid(raw_result, method: str) -> str:
    if not isinstance(raw_result, dict):
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"{method} returned an invalid response"))

    uuid = raw_result.get("uuid")
    if not isinstance(uuid, str) or not uuid:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"{method} did not return a block uuid"))

    return uuid


async def _insert_children(client, parent_uuid: str, children: list[WriteBlockInput]) -> int:
    appended = 0

    for child in children:
        child_result = await client._call(
            "logseq.Editor.insertBlock",
            parent_uuid,
            child.content,
            _mutation_options(child, child=True),
        )
        child_uuid = _extract_uuid(child_result, "logseq.Editor.insertBlock")
        appended += 1
        appended += await _insert_children(client, child_uuid, child.children)

    return appended


async def _append_tree_to_page(client, page_name: str, blocks: list[WriteBlockInput]) -> int:
    appended = 0

    for block in blocks:
        result = await client._call(
            "logseq.Editor.appendBlockInPage",
            page_name,
            block.content,
            _mutation_options(block),
        )
        block_uuid = _extract_uuid(result, "logseq.Editor.appendBlockInPage")
        appended += 1
        appended += await _insert_children(client, block_uuid, block.children)

    return appended


async def _get_page_or_error(client, page_name: str) -> PageEntity:
    raw = await client._call("logseq.Editor.getPage", page_name)
    if raw is None:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"page not found: {page_name}"))
    return PageEntity.model_validate(raw)


async def _get_page_or_none(client, page_name: str) -> PageEntity | None:
    raw = await client._call("logseq.Editor.getPage", page_name)
    if raw is None:
        return None

    try:
        return PageEntity.model_validate(raw)
    except ValidationError as exc:
        raise McpError(
            ErrorData(code=INTERNAL_ERROR, message=f"logseq.Editor.getPage returned an invalid response: {exc}")
        ) from exc


async def _verify_page_present(client, page_name: str) -> PageEntity:
    page = await _get_page_or_none(client, page_name)
    if page is None:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"page not found: {page_name}"))
    return page


async def _verify_page_absent(client, page_name: str) -> None:
    page = await _get_page_or_none(client, page_name)
    if page is not None:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"page still exists after delete: {page_name}"))


def _page_matches_name(page: PageEntity, expected_name: str) -> bool:
    if page.name.casefold() == expected_name.casefold():
        return True
    if isinstance(page.original_name, str) and page.original_name == expected_name:
        return True
    return False


def _validate_rename_target(old_name: str, new_name: str) -> None:
    if not isinstance(old_name, str) or not old_name.strip():
        raise McpError(ErrorData(code=INTERNAL_ERROR, message="old_name must be a non-empty string"))
    if not isinstance(new_name, str) or not new_name.strip():
        raise McpError(ErrorData(code=INTERNAL_ERROR, message="new_name must be a non-empty string"))
    if old_name == new_name:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message="new_name must differ from old_name"))


async def _verify_rename_target_available(client, new_name: str) -> None:
    page = await _get_page_or_none(client, new_name)
    if page is not None:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"page already exists: {new_name}"))


async def _verify_rename_readback(client, old_name: str, new_name: str) -> PageEntity:
    await _verify_page_absent(client, old_name)
    page = await _verify_page_present(client, new_name)
    if not _page_matches_name(page, new_name):
        raise McpError(
            ErrorData(code=INTERNAL_ERROR, message=f"renamed page did not resolve at new name: {new_name}")
        )
    return page


async def _get_page_blocks(client, page_name: str) -> list[BlockEntity]:
    raw = await client._call("logseq.Editor.getPageBlocksTree", page_name)
    if not isinstance(raw, list):
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"page block tree unavailable: {page_name}"))
    return _parse_block_tree(raw)


async def _get_block_or_error(client, uuid: str) -> BlockEntity:
    raw = await client._call("logseq.Editor.getBlock", uuid, {"includeChildren": True})
    if raw is None:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"block not found: {uuid}"))

    try:
        return BlockEntity.model_validate(raw)
    except ValidationError as exc:
        raise McpError(
            ErrorData(code=INTERNAL_ERROR, message=f"logseq.Editor.getBlock returned an invalid response: {exc}")
        ) from exc


async def _verify_block_readback(client, uuid: str, expected_content: str) -> BlockEntity:
    block = await _get_block_or_error(client, uuid)
    if block.content != expected_content:
        raise McpError(
            ErrorData(code=INTERNAL_ERROR, message=f"updated content did not match readback for block: {uuid}")
        )
    return block


async def _verify_block_absent(client, uuid: str, page_name: str | None = None) -> None:
    raw = await client._call("logseq.Editor.getBlock", uuid, {"includeChildren": True})
    if raw is not None:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"block still exists after delete: {uuid}"))

    if page_name:
        block_tree = await _get_page_blocks(client, page_name)
        if _contains_block_uuid(block_tree, uuid):
            raise McpError(
                ErrorData(code=INTERNAL_ERROR, message=f"block still present in page tree after delete: {uuid}")
            )


def _normalize_error(exc: Exception) -> McpError:
    if isinstance(exc, McpError):
        return exc
    if isinstance(exc, (ValidationError, ValueError, TypeError)):
        return McpError(ErrorData(code=INTERNAL_ERROR, message=str(exc)))
    raise exc


@mcp.tool()
async def page_create(
    ctx: Context,
    name: str,
    properties: dict | None = None,
    blocks: list | None = None,
) -> str:
    app_ctx: AppContext = ctx.request_context.lifespan_context
    client = app_ctx.client

    logger.info("page_create: %s", name)

    try:
        normalized_blocks = _normalize_blocks(blocks)
    except Exception as exc:
        raise _normalize_error(exc)

    page_properties = properties or {}
    if not isinstance(page_properties, dict):
        raise McpError(ErrorData(code=INTERNAL_ERROR, message="page properties must be a dict"))

    created = await client._call(
        "logseq.Editor.createPage",
        name,
        page_properties,
        {"createFirstBlock": False},
    )
    if created is None:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"failed to create page: {name}"))

    appended_count = await _append_tree_to_page(client, name, normalized_blocks)
    page = await _get_page_or_error(client, name)
    block_tree = await _get_page_blocks(client, name)

    return json.dumps(
        {
            "page": page.model_dump(by_alias=False),
            "created": True,
            "blocks": [block.model_dump(by_alias=False) for block in block_tree],
            "block_count": _count_blocks(block_tree),
            "appended": appended_count,
        }
    )


@mcp.tool()
async def block_append(ctx: Context, page: str, blocks: list | str | dict) -> str:
    app_ctx: AppContext = ctx.request_context.lifespan_context
    client = app_ctx.client

    logger.info("block_append: %s", page)

    try:
        normalized_blocks = _normalize_blocks(blocks)
    except Exception as exc:
        raise _normalize_error(exc)

    await _get_page_or_error(client, page)
    appended_count = await _append_tree_to_page(client, page, normalized_blocks)
    block_tree = await _get_page_blocks(client, page)

    return json.dumps(
        {
            "page": page,
            "appended": appended_count,
            "blocks": [block.model_dump(by_alias=False) for block in block_tree],
            "block_count": _count_blocks(block_tree),
        }
    )


@mcp.tool()
async def block_update(ctx: Context, uuid: str, content: str) -> str:
    app_ctx: AppContext = ctx.request_context.lifespan_context
    client = app_ctx.client

    logger.info("block_update: %s", uuid)

    await _get_block_or_error(client, uuid)

    await client._call("logseq.Editor.updateBlock", uuid, content)

    block = await _verify_block_readback(client, uuid, content)
    return json.dumps({"uuid": block.uuid, "content": block.content})


@mcp.tool()
async def block_delete(ctx: Context, uuid: str) -> str:
    app_ctx: AppContext = ctx.request_context.lifespan_context
    client = app_ctx.client

    logger.info("block_delete: %s", uuid)

    block = await _get_block_or_error(client, uuid)
    page_name = block.page.name if block.page and block.page.name else None

    await client._call("logseq.Editor.removeBlock", uuid)
    await _verify_block_absent(client, uuid, page_name)
    return json.dumps({"ok": True, "uuid": uuid})


@mcp.tool()
async def delete_page(ctx: Context, name: str) -> str:
    app_ctx: AppContext = ctx.request_context.lifespan_context
    client = app_ctx.client

    logger.info("delete_page: %s", name)

    await _verify_page_present(client, name)
    await client._call("logseq.Editor.deletePage", name)
    await _verify_page_absent(client, name)

    return json.dumps({"ok": True, "name": name})


@mcp.tool()
async def rename_page(ctx: Context, old_name: str, new_name: str) -> str:
    app_ctx: AppContext = ctx.request_context.lifespan_context
    client = app_ctx.client

    logger.info("rename_page: %s -> %s", old_name, new_name)

    _validate_rename_target(old_name, new_name)
    await _verify_page_present(client, old_name)
    await _verify_rename_target_available(client, new_name)
    await client._call("logseq.Editor.renamePage", old_name, new_name)
    await _verify_rename_readback(client, old_name, new_name)

    return json.dumps({"ok": True, "old_name": old_name, "new_name": new_name})
