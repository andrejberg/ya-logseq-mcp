from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator

from mcp.server.fastmcp import FastMCP, Context

from logseq_mcp.client import LogseqClient


@dataclass
class AppContext:
    client: LogseqClient


@asynccontextmanager
async def lifespan(app: FastMCP) -> AsyncIterator[AppContext]:
    client = LogseqClient()
    async with client:
        yield AppContext(client=client)


mcp = FastMCP("logseq-mcp", lifespan=lifespan)

# Import tools so they register their decorators on `mcp`
from logseq_mcp.tools import core as _core  # noqa: E402, F401
