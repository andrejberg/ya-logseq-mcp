# Architecture

**Analysis Date:** 2026-03-09

## Pattern Overview

**Overall:** Layered MCP server with async HTTP client facade over Logseq's RPC API

**Key Characteristics:**
- Single-process MCP server exposing 27 tools over stdio transport
- All tool handlers are `async def` coroutines using `httpx.AsyncClient`
- Tools grouped by domain (core, journal, kanban, templates, write) in separate modules
- Logseq HTTP API abstracted behind a single async client (`client.py`)
- Pydantic models provide type safety and flexible deserialization for Logseq's inconsistent JSON formats
- No local state or caching -- every call hits Logseq's HTTP API directly

## Layers

**Transport Layer (MCP SDK):**
- Purpose: Handle MCP protocol, tool registration, stdio communication
- Location: `src/logseq_mcp/server.py`
- Contains: MCP server instantiation, tool registration, tool handler wiring
- Depends on: `mcp` SDK
- Used by: MCP clients (Claude Code, other AI assistants)

**Tool Layer:**
- Purpose: Implement tool logic -- parameter validation, orchestration, response formatting
- Location: `src/logseq_mcp/tools/`
- Contains: One module per domain (`core.py`, `journal.py`, `kanban.py`, `templates.py`, `write.py`)
- Depends on: Client layer, Types layer
- Used by: Server layer (registered as MCP tool handlers)

**Client Layer:**
- Purpose: Async HTTP communication with Logseq's API, retry logic, auth
- Location: `src/logseq_mcp/client.py`
- Contains: `LogseqClient` class with methods mapping to Logseq API endpoints
- Depends on: `httpx`, Types layer
- Used by: Tool layer

**Types Layer:**
- Purpose: Pydantic models for Logseq entities (pages, blocks, refs)
- Location: `src/logseq_mcp/types.py`
- Contains: `PageEntity`, `BlockEntity`, `PageRef`, `BlockRef` models with custom validators
- Depends on: `pydantic`
- Used by: Client layer (response parsing), Tool layer (data manipulation)

## Data Flow

**Tool Invocation (read):**

1. MCP client sends `tools/call` request over stdio
2. `server.py` dispatches to registered tool handler in `tools/`
3. Tool handler calls `client.py` methods (e.g., `client.get_page()`)
4. `client.py` sends `POST /api` to Logseq with `{"method": "logseq.Editor.getPage", "args": [...]}`
5. Response JSON deserialized into Pydantic models (`PageEntity`, `BlockEntity`)
6. Tool handler applies domain logic (deduplication, filtering, formatting)
7. Result serialized to JSON text and returned as MCP `CallToolResult`

**Tool Invocation (write):**

1. MCP client sends `tools/call` with mutation parameters
2. Tool handler validates input, calls `client.py` write methods
3. `client.py` sends mutating `POST /api` (e.g., `logseq.Editor.appendBlockInPage`)
4. Logseq applies the change; response confirms success
5. Tool handler returns confirmation or the created/updated entity

**DataScript Query Flow:**

1. Tool handler constructs Clojure DataScript query string
2. `client.datascript_query()` sends query via `logseq.DB.datascriptQuery`
3. Raw JSON results returned and processed by tool handler
4. Used by: `find_by_tag`, `query_properties`, `query`, `get_references`

**State Management:**
- No local state. The MCP server is stateless; Logseq is the single source of truth.
- `httpx.AsyncClient` may be reused across requests for connection pooling.

## Key Abstractions

**LogseqClient (`client.py`):**
- Purpose: Wrap Logseq's HTTP API with typed async methods
- Pattern: Facade -- translates typed method calls to `POST /api` JSON-RPC
- Reference implementation: `graphthulhu/client/logseq.go` (Go version with retry + backoff)
- Key behavior: Retry with exponential backoff on server errors (5xx), no retry on client errors (4xx)
- Auth: `Bearer` token from `LOGSEQ_API_TOKEN` env var

**Pydantic Entity Models (`types.py`):**
- Purpose: Deserialize Logseq's JSON with format flexibility
- Examples: `PageEntity`, `BlockEntity`, `PageRef`, `BlockRef`
- Pattern: Pydantic models with custom validators to handle Logseq returning refs as either `{"id": N}` or plain `N`
- Reference: `graphthulhu/types/logseq.go` -- same fields, Go struct tags

**Block Tree Deduplication (planned in `tools/core.py`):**
- Purpose: Fix graphthulhu's block duplication bug (blocks returned 4-8x)
- Pattern: Deduplicate by UUID when walking the block tree from `getPageBlocksTree`
- Critical difference from graphthulhu: this is the primary motivation for the rewrite

**Tool Modules (`tools/*.py`):**
- Purpose: Group related tools by domain
- Pattern: Each module exports async handler functions; `server.py` imports and registers them
- Reference: graphthulhu uses struct-based grouping (`tools.NewNavigate(b)`, `tools.NewSearch(b)`)

## Entry Points

**`src/logseq_mcp/__main__.py`:**
- Location: `src/logseq_mcp/__main__.py`
- Triggers: `python -m logseq_mcp` or `uv run python -m logseq_mcp`
- Responsibilities: Parse config from env vars, create client, create and run MCP server

**`pyproject.toml` script entry:**
- Location: `pyproject.toml` line 17
- Script: `logseq-mcp = "logseq_mcp.__main__:main"`
- Triggers: `uv run logseq-mcp` after install

## Error Handling

**Strategy:** Return errors as MCP tool results (not exceptions). Match graphthulhu's pattern of `errorResult()` -- set `isError: true` on the `CallToolResult`.

**Patterns:**
- Client layer: Retry on 5xx with exponential backoff (100ms initial, 3 retries). Raise on 4xx immediately.
- Tool layer: Catch client errors, return user-friendly error messages in `CallToolResult.content` with `isError=True`.
- Never crash the server on a single tool call failure.

## Cross-Cutting Concerns

**Logging:** Not yet implemented. Plan: use Python `logging` module. The MCP SDK may provide logging hooks.

**Validation:** Pydantic models validate API responses. Tool input validation handled by MCP SDK schema enforcement + Pydantic.

**Authentication:** Bearer token from `LOGSEQ_API_TOKEN` env var, sent as `Authorization` header on every request.

**Configuration:** Two env vars only:
- `LOGSEQ_API_URL` (default: `http://127.0.0.1:12315`)
- `LOGSEQ_API_TOKEN` (required)

## Reference Architecture (graphthulhu)

The `graphthulhu/` directory contains the Go implementation being replaced. Key architectural differences:

| Aspect | graphthulhu (Go) | logseq-mcp (Python) |
|--------|-----------------|---------------------|
| Backend abstraction | `backend.Backend` interface supporting Logseq + Obsidian | No backend interface -- Logseq only |
| HTTP client | Sync `net/http` with manual retry | Async `httpx.AsyncClient` with retry |
| Tool grouping | Struct methods (`Navigate.GetPage`) | Module-level async functions |
| Content parsing | `parser/content.go` extracts links/tags | Not replicated -- lean output by default |
| Graph analysis | `graph/` package builds in-memory graph | Not implemented -- not needed |
| Block enrichment | Always enriches with parsed content | Lean by default; no parsed links/tags/ancestors |

**Files to reference during implementation:**
- `graphthulhu/client/logseq.go` -- API call patterns, retry logic
- `graphthulhu/types/logseq.go` -- entity models, JSON unmarshaling quirks
- `graphthulhu/tools/navigate.go` -- `get_page` deduplication target, `get_block`, `list_pages`
- `graphthulhu/tools/search.go` -- DataScript query patterns for `find_by_tag`, `query_properties`
- `graphthulhu/tools/write.go` -- write tool implementations
- `graphthulhu/tools/journal.go` -- journal date format handling
- `graphthulhu/server.go` -- tool registration pattern
- `graphthulhu/backend/backend.go` -- interface contract (subset to implement)

---

*Architecture analysis: 2026-03-09*
