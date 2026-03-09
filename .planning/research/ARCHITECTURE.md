# Architecture Patterns

**Domain:** Python MCP server wrapping Logseq HTTP API
**Researched:** 2026-03-09

## Recommended Architecture

Four-layer architecture with dependency injection via MCP SDK lifespan.

```
MCP Client (Claude Code)
    |  stdio (JSON-RPC)
    v
[Transport Layer]  server.py — FastMCP instance, tool registration
    |
    v
[Tool Layer]  tools/{core,write,journal}.py — domain logic, validation, response formatting
    |
    v
[Client Layer]  client.py — LogseqClient, async HTTP facade, retry
    |  httpx POST /api
    v
[Types Layer]  types.py — Pydantic models (PageEntity, BlockEntity, refs)
    |
    v
Logseq Desktop (HTTP API on :12315)
```

### Component Boundaries

| Component | Responsibility | Communicates With | Owns |
|-----------|---------------|-------------------|------|
| `server.py` | FastMCP instance, tool registration, lifespan (client lifecycle), entry point | Tool layer (registers handlers), Client layer (creates in lifespan) | MCP protocol concerns, tool metadata/descriptions |
| `tools/core.py` | Read tool logic: `get_page`, `get_block`, `list_pages`, `get_references`, `find_by_tag`, `query_properties`, `query` | Client layer (calls API methods), Types layer (uses models) | Block deduplication, DataScript query construction, response formatting |
| `tools/write.py` | Write tool logic: `page_create`, `block_append`, `block_update`, `block_delete`, `delete_page`, `rename_page`, `move_block` | Client layer (calls API methods) | Input validation for writes, nested block construction |
| `tools/journal.py` | Journal tools: `journal_today`, `journal_append`, `journal_range` | Client layer, Tools/core (reuses `get_page` for reading journal pages) | Date format handling, date range iteration |
| `client.py` | Async HTTP communication with Logseq API | Types layer (deserializes into models), httpx (HTTP transport) | Retry logic, auth headers, API method mapping, connection pooling |
| `types.py` | Pydantic models for Logseq entities | Nothing (leaf dependency) | Data shapes, JSON deserialization quirks, ref format normalization |

### Data Flow

**Read path (e.g., `get_page`):**

```
1. MCP client sends tools/call {"name": "get_page", "arguments": {"name": "Projects"}}
2. FastMCP dispatches to registered async handler in tools/core.py
3. Handler gets LogseqClient from module-level reference (set during lifespan)
4. Handler calls client.get_page("Projects") -> client.get_page_blocks_tree("Projects")
5. client.py POSTs {"method": "logseq.Editor.getPage", "args": ["Projects"]} to :12315/api
6. Response JSON -> Pydantic model (PageEntity, list[BlockEntity])
7. Handler deduplicates blocks by UUID, builds clean tree
8. Handler returns JSON string as TextContent in CallToolResult
```

**Write path (e.g., `block_append`):**

```
1. MCP client sends tools/call with page name + block content
2. Handler validates input (flat strings vs nested objects)
3. For flat: calls client.append_block_in_page(page, content) per block
4. For nested: calls client.insert_block(parent_uuid, content, opts) recursively
5. Each call POSTs to Logseq API, returns created BlockEntity
6. Handler returns confirmation with created block UUIDs
```

**DataScript query path (e.g., `find_by_tag`):**

```
1. Handler constructs Clojure query string from tool parameters
2. Calls client.datascript_query(query_string)
3. client.py POSTs {"method": "logseq.DB.datascriptQuery", "args": [query]}
4. Raw JSON result (nested arrays) returned to handler
5. Handler processes raw results into structured response
```

## Patterns to Follow

### Pattern 1: FastMCP Lifespan for Client Lifecycle

**What:** Use FastMCP's `lifespan` parameter to create and tear down the `httpx.AsyncClient` (and the `LogseqClient` wrapper). This ensures proper connection pool management.

**Why:** `httpx.AsyncClient` must be used as an async context manager for proper cleanup. The lifespan pattern is the MCP SDK's intended mechanism for managing shared async resources.

**Confidence:** HIGH -- verified in MCP SDK v1.26.0 source code.

**Example:**

```python
# server.py
from contextlib import asynccontextmanager
from mcp.server.fastmcp import FastMCP, Context

from logseq_mcp.client import LogseqClient

_client: LogseqClient | None = None

@asynccontextmanager
async def lifespan(server: FastMCP):
    global _client
    async with LogseqClient.create() as client:
        _client = client
        yield
    _client = None

def get_client() -> LogseqClient:
    """Get the active LogseqClient. Raises if called outside lifespan."""
    if _client is None:
        raise RuntimeError("LogseqClient not initialized -- server not running")
    return _client

mcp = FastMCP("logseq-mcp", lifespan=lifespan)
```

**Rationale for module-level global over Context.lifespan_context:** The MCP SDK's `Context` object is available inside tool handlers, but accessing `ctx.request_context.lifespan_context` is verbose and couples tool code to MCP internals. A module-level `get_client()` is simpler and testable -- in tests, you set `_client` directly.

### Pattern 2: Tool Registration via Decorators

**What:** Use `@mcp.tool()` decorator to register each tool handler. Each tool is a standalone async function in its domain module.

**Why:** FastMCP's decorator pattern auto-generates JSON Schema from function signatures and type hints. This eliminates manual schema definitions (which graphthulhu's Go version had to do manually with `json.RawMessage`).

**Confidence:** HIGH -- this is FastMCP's primary API.

**Example:**

```python
# tools/core.py
from logseq_mcp.server import mcp, get_client

@mcp.tool(
    name="get_page",
    description="Get a page with its block tree, deduplicated by UUID."
)
async def get_page(name: str, include_children: bool = True) -> str:
    client = get_client()
    page = await client.get_page(name)
    blocks = await client.get_page_blocks_tree(name)
    deduped = _deduplicate_blocks(blocks)
    return json.dumps({"page": page.model_dump(), "blocks": deduped})
```

### Pattern 3: Circular Import Avoidance

**What:** `server.py` creates the `FastMCP` instance and exports it. Tool modules import from `server.py`. But `server.py` must not import tool modules at module level -- tools register themselves via decorators when their modules are imported.

**Why:** Tool modules need `mcp` from `server.py` for `@mcp.tool()`. If `server.py` also imports tool modules, you get circular imports.

**Resolution:** `__main__.py` imports tool modules after `server.py`, triggering decorator registration.

**Example:**

```python
# __main__.py
def main():
    from logseq_mcp.server import mcp  # creates FastMCP instance

    # Import tool modules to trigger @mcp.tool() registration
    import logseq_mcp.tools.core      # noqa: F401
    import logseq_mcp.tools.write     # noqa: F401
    import logseq_mcp.tools.journal   # noqa: F401

    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
```

### Pattern 4: Error Handling as Tool Results

**What:** Tool handlers catch exceptions and return error messages via the MCP SDK's error mechanism, never crashing the server process.

**Why:** A single tool failure must not kill the MCP server. graphthulhu uses `errorResult()` with `isError: true`. FastMCP handles this by raising `ToolError` or returning error content.

**Confidence:** HIGH -- verified in SDK source.

**Example:**

```python
from mcp.server.fastmcp import Context

@mcp.tool(name="get_page")
async def get_page(name: str) -> str:
    client = get_client()
    try:
        page = await client.get_page(name)
        if page is None:
            raise ValueError(f"Page not found: {name}")
        # ... process and return
    except Exception as e:
        # FastMCP converts raised exceptions to isError=True responses
        raise
```

### Pattern 5: Client as Async Context Manager

**What:** `LogseqClient` wraps `httpx.AsyncClient` and exposes itself as an async context manager for proper resource lifecycle.

**Why:** `httpx.AsyncClient` manages a connection pool internally. Using it as a context manager ensures connections are closed on shutdown. This avoids ResourceWarning and leaked sockets.

**Confidence:** HIGH -- httpx documented pattern.

**Example:**

```python
# client.py
class LogseqClient:
    def __init__(self, api_url: str, token: str, http_client: httpx.AsyncClient):
        self._api_url = api_url
        self._token = token
        self._http = http_client

    @classmethod
    @asynccontextmanager
    async def create(cls, api_url: str | None = None, token: str | None = None):
        url = api_url or os.environ.get("LOGSEQ_API_URL", "http://127.0.0.1:12315")
        tok = token or os.environ["LOGSEQ_API_TOKEN"]
        async with httpx.AsyncClient(
            base_url=url,
            timeout=10.0,
            headers={"Authorization": f"Bearer {tok}"}
        ) as http:
            yield cls(url, tok, http)
```

### Pattern 6: Block Tree Deduplication

**What:** After fetching blocks via `getPageBlocksTree`, deduplicate by UUID before returning. Walk the tree, track seen UUIDs, skip duplicates.

**Why:** This is the primary motivation for the rewrite. graphthulhu's recursive traversal produces 4-8x block duplication. The Logseq API itself returns a flat-ish tree with children embedded; the duplication comes from re-traversing children that are already in the tree.

**Implementation note:** Deduplication belongs in the tool layer (`tools/core.py`), not the client layer. The client should return raw API responses faithfully. The tool layer applies domain logic like deduplication.

```python
def _deduplicate_blocks(blocks: list[BlockEntity]) -> list[dict]:
    """Walk block tree, deduplicate by UUID, return clean dicts."""
    seen: set[str] = set()
    result = []
    for block in blocks:
        if block.uuid in seen:
            continue
        seen.add(block.uuid)
        node = block.model_dump(exclude={"children"})
        if block.children:
            node["children"] = _deduplicate_blocks(block.children)
        result.append(node)
    return result
```

## Anti-Patterns to Avoid

### Anti-Pattern 1: Creating httpx.AsyncClient Per Request

**What:** Instantiating `httpx.AsyncClient()` inside each tool handler call.
**Why bad:** No connection reuse, TCP connection setup overhead on every request. For a tool like `block_append` that makes multiple sequential API calls, this adds significant latency.
**Instead:** Create one `httpx.AsyncClient` in the lifespan, reuse via `LogseqClient` instance.

### Anti-Pattern 2: Putting Domain Logic in the Client Layer

**What:** Adding deduplication, DataScript query construction, or response formatting to `client.py`.
**Why bad:** The client becomes untestable -- you can't test raw API behavior separately from domain logic. Client methods should be thin wrappers: take arguments, call API, return typed response.
**Instead:** Client returns raw typed responses. Tool handlers apply domain logic (deduplication, query construction, formatting).

### Anti-Pattern 3: Synchronous HTTP Calls

**What:** Using `httpx.Client` (sync) or `requests` instead of `httpx.AsyncClient`.
**Why bad:** MCP tools can be called concurrently. Sync HTTP blocks the event loop, preventing other tools from executing. Even though Logseq's API is local, journal_range might make 30 sequential date lookups -- async lets other tools proceed.
**Instead:** Async throughout. Already decided in project spec.

### Anti-Pattern 4: Tool Modules Importing Each Other

**What:** `tools/journal.py` importing from `tools/core.py` to reuse `get_page` logic.
**Why bad:** Creates coupling between tool modules. Changes to `get_page` response format break journal tools. Tool modules should be independent.
**Instead:** Both modules call `client.py` methods directly. If shared logic is needed (e.g., block tree processing), extract to a utility function in a separate module or in `types.py`.

### Anti-Pattern 5: Returning Pydantic Models Directly from Tools

**What:** Returning `PageEntity` objects directly as tool results.
**Why bad:** MCP tools return text content (or images/embedded resources). Pydantic models need explicit serialization. FastMCP can auto-serialize return values, but the format may not be what you want (e.g., including internal fields like `pre_block`).
**Instead:** Explicitly serialize to JSON with `model_dump(exclude=...)` to control what the LLM sees. Lean output is a key design goal.

## Component Build Order

Dependencies flow downward. Build from the bottom up.

```
Phase 1: Foundation (no inter-dependencies)
  1. types.py        — zero deps, leaf node
  2. client.py       — depends on types.py + httpx
  3. server.py       — depends on client.py (lifespan), FastMCP
  4. __main__.py     — depends on server.py (thin entry point)
  5. health tool     — verify end-to-end: MCP -> server -> client -> Logseq

Phase 2: Core Reads (depends on Phase 1)
  6. tools/core.py   — all read tools, depends on client + types
     - get_page (with deduplication) first -- most critical
     - get_block, list_pages, get_references
     - query, find_by_tag, query_properties

Phase 3: Writes (depends on Phase 1, independent of Phase 2)
  7. tools/write.py  — all write tools, depends on client + types
     - page_create, block_append first
     - block_update, block_delete, delete_page, rename_page, move_block

Phase 4: Journal (depends on Phase 1, partially on Phase 2 patterns)
  8. tools/journal.py — journal tools, depends on client + types
     - journal_today, journal_append, journal_range
```

**Why this order:**
- Types must exist before client can deserialize responses
- Client must exist before any tool can call the API
- Server + lifespan must exist before tools can register via `@mcp.tool()`
- `health` tool validates the entire stack end-to-end before building business logic
- Core reads before writes because reads are needed to verify writes work correctly
- Journal is independent of core/write but benefits from patterns established there

## Scalability Considerations

Not applicable in the traditional sense -- this is a single-user local MCP server. However:

| Concern | Current Design | If It Mattered |
|---------|---------------|----------------|
| Concurrent tool calls | Async handlers + connection pooling via httpx | Already handled |
| Large pages (1000+ blocks) | Deduplication + lean output | Could add pagination via `max_blocks` parameter |
| Many sequential API calls (journal_range) | Async but sequential per tool | Could use `asyncio.gather()` for parallel fetches |
| Logseq API latency | 10s timeout, 3 retries with exponential backoff | Already handled |

## Key Architecture Decisions

| Decision | Rationale |
|----------|-----------|
| FastMCP (bundled in mcp SDK) over low-level Server | Decorator-based tool registration, auto schema generation, lifespan support. No reason to use low-level API. |
| Module-level `_client` global over Context.lifespan_context | Simpler access in tool handlers, easier to test (mock by setting global), avoids coupling to MCP Context internals |
| Client returns typed Pydantic models, tools format output | Clean separation: client = API faithfulness, tools = domain logic + LLM-friendly formatting |
| Deduplication in tool layer, not client layer | Client should reflect what the API returns. Deduplication is domain logic that fixes a known Logseq API quirk. |
| `@mcp.tool()` decorator in tool modules, imported by `__main__.py` | Avoids circular imports. Tool modules are self-registering when imported. |
| stdio transport only | MCP clients (Claude Code) use stdio. No need for SSE or HTTP transport. |

## Sources

- MCP Python SDK v1.26.0 source code (installed, verified in `.venv/`)
- [MCP Python SDK GitHub](https://github.com/modelcontextprotocol/python-sdk) -- HIGH confidence
- [FastMCP server documentation](https://gofastmcp.com/python-sdk/fastmcp-server-server) -- MEDIUM confidence (standalone FastMCP docs, API compatible with bundled version)
- graphthulhu Go reference implementation (`graphthulhu/server.go`, `graphthulhu/client/logseq.go`) -- HIGH confidence (direct source)
- httpx documentation for AsyncClient lifecycle -- HIGH confidence

---

*Architecture research: 2026-03-09*
