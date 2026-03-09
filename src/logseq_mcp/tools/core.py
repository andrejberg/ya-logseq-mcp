import json
import logging

from mcp import McpError
from mcp.types import ErrorData, INTERNAL_ERROR
from mcp.server.fastmcp import Context

from logseq_mcp.server import mcp, AppContext
from logseq_mcp.types import BlockEntity, PageEntity

logger = logging.getLogger(__name__)


@mcp.tool()
async def health(ctx: Context) -> str:
    """Ping Logseq and return graph name and page count."""
    app_ctx: AppContext = ctx.request_context.lifespan_context
    client = app_ctx.client

    logger.info("health: checking Logseq connectivity")

    graph = await client._call("logseq.App.getCurrentGraph")
    pages = await client._call("logseq.Editor.getAllPages")

    graph_name = graph.get("name", "unknown") if isinstance(graph, dict) else "unknown"
    page_count = len(pages) if isinstance(pages, list) else 0

    return json.dumps({"status": "ok", "graph": graph_name, "page_count": page_count})


def _count_blocks(blocks: list[BlockEntity]) -> int:
    total = 0
    for block in blocks:
        total += 1 + _count_blocks(block.children)
    return total


def _dedup_children(children: list[BlockEntity], seen: set[str]) -> list[BlockEntity]:
    filtered: list[BlockEntity] = []
    for child in children:
        if child.uuid in seen:
            continue
        seen.add(child.uuid)
        child.children = _dedup_children(child.children, seen)
        filtered.append(child)
    return filtered


def _parse_block_tree(raw_blocks: list) -> list[BlockEntity]:
    seen: set[str] = set()
    parsed: list[BlockEntity] = []

    for raw_block in raw_blocks:
        block = BlockEntity.model_validate(raw_block)
        if block.uuid in seen:
            continue
        seen.add(block.uuid)
        block.children = _dedup_children(block.children, seen)
        parsed.append(block)

    return parsed


@mcp.tool()
async def get_page(ctx: Context, name: str) -> str:
    """Return a page entity and deduplicated block tree by page name."""
    app_ctx: AppContext = ctx.request_context.lifespan_context
    client = app_ctx.client

    logger.info("get_page: fetching page %s", name)

    page_raw = await client._call("logseq.Editor.getPage", name)
    if page_raw is None:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"page not found: {name}"))

    page = PageEntity.model_validate(page_raw)

    blocks_result = await client._call("logseq.Editor.getPageBlocksTree", name)
    blocks_raw = blocks_result if isinstance(blocks_result, list) else []
    blocks = _parse_block_tree(blocks_raw)

    return json.dumps(
        {
            "page": page.model_dump(by_alias=False),
            "blocks": [block.model_dump(by_alias=False) for block in blocks],
            "block_count": _count_blocks(blocks),
        }
    )


@mcp.tool()
async def get_block(ctx: Context, uuid: str, include_children: bool = True) -> str:
    """Get a single block by UUID."""
    app_ctx: AppContext = ctx.request_context.lifespan_context
    client = app_ctx.client

    logger.info("get_block: %s", uuid)

    opts = {"includeChildren": include_children}
    raw = await client._call("logseq.Editor.getBlock", uuid, opts)
    if raw is None:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"block not found: {uuid}"))

    block = BlockEntity.model_validate(raw)
    return json.dumps(block.model_dump(by_alias=False))
