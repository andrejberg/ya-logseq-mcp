# Phase 1: Foundation - Context

**Gathered:** 2026-03-09
**Status:** Ready for planning

<domain>
## Phase Boundary

A running MCP server that connects to Logseq over HTTP, handles auth, serializes concurrent requests, and responds to health checks. No read or write tools yet — just the plumbing that every subsequent phase depends on.

</domain>

<decisions>
## Implementation Decisions

### Error handling policy
- Raise `McpError` (MCP SDK exception) with a clear human-readable message when Logseq is unreachable or returns unexpected data
- No structured JSON error envelopes — Claude should see the error directly as a tool failure
- Distingush two error classes: connectivity errors ("Logseq is not running or unreachable at {url}") and API errors ("Logseq API error {status}: {body}")

### Retry scope
- Retry on both 5xx HTTP errors AND connection errors / timeouts (not just 5xx as spec'd)
- Rationale: Logseq desktop takes a moment to start; connection refused is the most common failure in practice
- 3 retries, 100ms initial delay, exponential backoff — as per FOUN-02
- No retry on 4xx (bad request / auth failure) — those are client errors, not transient

### Config loading
- Environment variables only: `LOGSEQ_API_URL` and `LOGSEQ_API_TOKEN`
- No .env file loading — user sets vars in shell or MCP config
- Fail fast at startup if `LOGSEQ_API_TOKEN` is missing (clear error message)
- `LOGSEQ_API_URL` defaults to `http://127.0.0.1:12315`

### Logging verbosity
- INFO level: log server start, tool calls (name + args summary), and errors
- No per-request body/response traces at INFO — keep stderr readable during normal use
- DEBUG level available for full request/response traces during development

### Claude's Discretion
- Exact backoff algorithm (linear vs exponential within the 3-retry window)
- asyncio.Semaphore placement (client constructor vs module-level)
- Pydantic model field names and validator implementation details
- FastMCP lifespan context manager implementation

</decisions>

<specifics>
## Specific Ideas

- Priority is a working prototype — correctness over polish
- Personal single-user tool: no need for multi-tenancy, complex config, or graceful degradation beyond "is Logseq running?"
- The health tool output should be immediately useful for confirming connectivity: graph name + page count is sufficient

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `pyproject.toml`: deps already pinned (`mcp>=1.0.0`, `httpx>=0.27.0`, `pydantic>=2.0.0`)
- `src/logseq_mcp/tools/__init__.py`: empty stub, ready for tool module registration
- `src/logseq_mcp/__main__.py`: empty, will hold `main()` entry point

### Established Patterns
- uv for dependency management and running (`uv run python -m logseq_mcp`)
- No existing server/client/types files — building from scratch
- graphthulhu source available at `graphthulhu/` as reference for API call patterns

### Integration Points
- `__main__.py` → calls `server.py` `main()` → FastMCP stdio transport
- `server.py` creates `httpx.AsyncClient` in lifespan, passes to tool handlers via context
- Tool handlers in `tools/` import client from context, call `client.py` methods

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 01-foundation*
*Context gathered: 2026-03-09*
