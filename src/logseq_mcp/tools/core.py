import json
import logging

from mcp.server.fastmcp import Context

from logseq_mcp.server import mcp, AppContext

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
