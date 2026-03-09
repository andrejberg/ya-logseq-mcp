# Phase 1: Foundation - Research

**Researched:** 2026-03-09
**Domain:** Python MCP server with FastMCP, httpx async client, Pydantic v2
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Error handling policy**
- Raise `McpError` (MCP SDK exception) with a clear human-readable message when Logseq is unreachable or returns unexpected data
- No structured JSON error envelopes — Claude should see the error directly as a tool failure
- Distinguish two error classes: connectivity errors ("Logseq is not running or unreachable at {url}") and API errors ("Logseq API error {status}: {body}")

**Retry scope**
- Retry on both 5xx HTTP errors AND connection errors / timeouts (not just 5xx as spec'd)
- Rationale: Logseq desktop takes a moment to start; connection refused is the most common failure in practice
- 3 retries, 100ms initial delay, exponential backoff — as per FOUN-02
- No retry on 4xx (bad request / auth failure) — those are client errors, not transient

**Config loading**
- Environment variables only: `LOGSEQ_API_URL` and `LOGSEQ_API_TOKEN`
- No .env file loading — user sets vars in shell or MCP config
- Fail fast at startup if `LOGSEQ_API_TOKEN` is missing (clear error message)
- `LOGSEQ_API_URL` defaults to `http://127.0.0.1:12315`

**Logging verbosity**
- INFO level: log server start, tool calls (name + args summary), and errors
- No per-request body/response traces at INFO — keep stderr readable during normal use
- DEBUG level available for full request/response traces during development

### Claude's Discretion
- Exact backoff algorithm (linear vs exponential within the 3-retry window)
- asyncio.Semaphore placement (client constructor vs module-level)
- Pydantic model field names and validator implementation details
- FastMCP lifespan context manager implementation

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| FOUN-01 | Async HTTP client connects to Logseq API with Bearer token auth | `httpx.AsyncClient` with `Authorization: Bearer` header; verified pattern below |
| FOUN-02 | Client retries on 5xx errors with exponential backoff (100ms initial, 3 retries) | `httpx.TransportError` catches ConnectError/TimeoutException; 5xx check on status code; backoff *= 2 pattern from graphthulhu |
| FOUN-03 | Client serializes requests with asyncio.Semaphore(1) to avoid Logseq UI freezes | `asyncio.Semaphore(1)` verified; place in `LogseqClient.__init__`, acquire inside `_call()` |
| FOUN-04 | Pydantic models handle polymorphic API responses (both `{"id": N}` and bare `N` formats) | `model_validator(mode='before')` pattern verified; converts int -> dict before field parsing |
| FOUN-05 | MCP server registers tools via FastMCP `@mcp.tool()` decorators | `FastMCP.tool()` decorator verified in mcp 1.26.0; function name becomes tool name |
| FOUN-06 | All logging goes to stderr only (stdout breaks MCP protocol) | `logging.basicConfig(stream=sys.stderr)` — verified; stdout reserved for JSON-RPC |
| FOUN-07 | `health` tool pings Logseq and returns graph name + page count | Uses `logseq.App.getCurrentGraph` + `logseq.Editor.getAllPages`; response shape documented |
| FOUN-08 | Server manages httpx.AsyncClient lifecycle via FastMCP lifespan | `@asynccontextmanager` lifespan yielding a `@dataclass` AppContext; accessed via `ctx.request_context.lifespan_context` |
</phase_requirements>

---

## Summary

Phase 1 builds the plumbing every subsequent phase depends on: a `FastMCP` server that runs over stdio, an async `httpx` HTTP client with retry/backoff/serialization, Pydantic v2 models for Logseq's polymorphic response types, and a single `health` tool that proves end-to-end connectivity.

The stack is fully pinned in `uv.lock`: mcp 1.26.0, httpx 0.28.1, pydantic 2.12.5, pytest 9.0.2, pytest-asyncio 1.3.0. Every pattern in this document has been verified against those exact versions. The graphthulhu Go reference (`graphthulhu/client/logseq.go`, `graphthulhu/types/logseq.go`) provides a proven blueprint; the Python translation is straightforward with no behavioral differences.

The one non-obvious challenge is how FastMCP exposes the lifespan-created `httpx.AsyncClient` to tool handlers. The path is: lifespan yields a dataclass → stored as `request_context.lifespan_context` → accessed in tool via `ctx: Context` parameter. This pattern is verified to compile and register correctly.

**Primary recommendation:** Implement in this order: `types.py` → `client.py` → `server.py` + `__main__.py` → `health` tool. The graphthulhu Go client is a direct blueprint for `client.py`; translate method-by-method.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| mcp (FastMCP) | 1.26.0 | MCP server framework, tool registration, stdio transport | Official Python MCP SDK; FastMCP provides decorator-based tool registration |
| httpx | 0.28.1 | Async HTTP client for Logseq API calls | Project standard; async-native, clean exception hierarchy, used in CLAUDE.md |
| pydantic | 2.12.5 | Data models, validation, polymorphic deserialization | Project standard; v2 `model_validator` handles int-or-dict refs cleanly |
| asyncio | stdlib | Semaphore for request serialization | No extra dependency; `asyncio.Semaphore(1)` is the correct tool |

### Dev / Test
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | 9.0.2 | Test runner | All tests |
| pytest-asyncio | 1.3.0 | async test support | All `async def test_*` functions |

**Installation:** Already present in `pyproject.toml` and `uv.lock`. No new deps needed for Phase 1.

```bash
uv sync  # installs from uv.lock
```

---

## Architecture Patterns

### Recommended Project Structure
```
src/logseq_mcp/
├── __init__.py          # keep minimal (currently has hello() stub — can leave or clear)
├── __main__.py          # main() entry point: configure logging, call mcp.run()
├── server.py            # FastMCP instance, lifespan, tool imports
├── client.py            # LogseqClient: _call(), retry, semaphore, typed helpers
├── types.py             # Pydantic models: PageEntity, BlockEntity, BlockRef, PageRef
└── tools/
    ├── __init__.py      # empty stub (already exists)
    └── core.py          # health tool (Phase 1 only — other tools come later)
```

### Pattern 1: FastMCP Lifespan with httpx.AsyncClient

The lifespan function creates the `httpx.AsyncClient` once at server startup and makes it available to all tool handlers via `ctx.request_context.lifespan_context`.

```python
# server.py
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator
import httpx
from mcp.server.fastmcp import FastMCP, Context

@dataclass
class AppContext:
    client: "LogseqClient"  # imported from client.py

@asynccontextmanager
async def lifespan(app: FastMCP) -> AsyncIterator[AppContext]:
    # LogseqClient wraps httpx.AsyncClient
    client = LogseqClient()
    async with client:          # client.__aenter__ opens httpx.AsyncClient
        yield AppContext(client=client)

mcp = FastMCP("logseq-mcp", lifespan=lifespan)
```

```python
# Tool accesses the client via ctx
@mcp.tool()
async def health(ctx: Context) -> str:
    app_ctx: AppContext = ctx.request_context.lifespan_context
    return await app_ctx.client.health()
```

**Verified:** Pattern compiles and registers tool correctly with mcp 1.26.0.

### Pattern 2: LogseqClient with Retry, Semaphore, and Auth

Translates directly from `graphthulhu/client/logseq.go`:

```python
# client.py
import asyncio
import os
import httpx
from mcp import McpError
from mcp.types import ErrorData, INTERNAL_ERROR

class LogseqClient:
    def __init__(self):
        self._url = os.environ.get("LOGSEQ_API_URL", "http://127.0.0.1:12315")
        self._token = os.environ.get("LOGSEQ_API_TOKEN", "")
        self._sem = asyncio.Semaphore(1)   # serialize all Logseq calls
        self._http: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "LogseqClient":
        self._http = httpx.AsyncClient(timeout=10.0)
        return self

    async def __aexit__(self, *exc) -> None:
        if self._http:
            await self._http.aclose()

    async def _call(self, method: str, *args) -> object:
        payload = {"method": method, "args": list(args)}
        headers = {"Authorization": f"Bearer {self._token}"}
        backoff = 0.1  # seconds
        last_err: Exception | None = None

        async with self._sem:
            for attempt in range(4):  # 1 initial + 3 retries
                if attempt > 0:
                    await asyncio.sleep(backoff)
                    backoff *= 2
                try:
                    resp = await self._http.post(
                        f"{self._url}/api",
                        json=payload,
                        headers=headers,
                    )
                except httpx.TransportError as e:
                    last_err = e
                    continue  # retry on connect errors and timeouts
                if resp.status_code >= 500:
                    last_err = Exception(f"Logseq API error {resp.status_code}: {resp.text}")
                    continue  # retry server errors
                if resp.status_code != 200:
                    # 4xx — client error, don't retry
                    raise McpError(ErrorData(
                        code=INTERNAL_ERROR,
                        message=f"Logseq API error {resp.status_code}: {resp.text}"
                    ))
                return resp.json()
        # Exhausted retries
        if isinstance(last_err, httpx.ConnectError):
            raise McpError(ErrorData(
                code=INTERNAL_ERROR,
                message=f"Logseq is not running or unreachable at {self._url}"
            ))
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=str(last_err)))
```

**Key details verified from graphthulhu source:**
- Backoff multiplies by 2 each retry (100ms → 200ms → 400ms)
- `httpx.TransportError` is the base class for `ConnectError`, `ConnectTimeout`, `ReadTimeout`, `NetworkError`, etc. — catches all transient failures
- 5xx retried; 4xx not retried; `ConnectError` retried

### Pattern 3: Pydantic v2 Polymorphic Refs

Logseq returns `parent`, `left`, and `page` fields as either `{"id": N}` (full objects) or bare `N` (integers from write responses). Use `model_validator(mode='before')`:

```python
# types.py
from pydantic import BaseModel, model_validator, Field
from typing import Any

class BlockRef(BaseModel):
    id: int

    @model_validator(mode='before')
    @classmethod
    def coerce_int(cls, v: Any) -> Any:
        if isinstance(v, int):
            return {"id": v}
        return v

class PageRef(BaseModel):
    id: int
    name: str = ""

    @model_validator(mode='before')
    @classmethod
    def coerce_int(cls, v: Any) -> Any:
        if isinstance(v, int):
            return {"id": v}
        return v
```

**Verified:** Both `BlockRef.model_validate(42)` and `BlockRef.model_validate({"id": 42})` produce identical results.

### Pattern 4: Compact Children Handling in BlockEntity

`getPageBlocksTree` returns children as full `BlockEntity` objects. `getBlock` returns them as compact `[["uuid", "value"], ...]` tuples. Silently skip compact form (leave `children` empty):

```python
class BlockEntity(BaseModel):
    id: int = 0
    uuid: str = ""
    content: str = ""
    children: list["BlockEntity"] = Field(default_factory=list)
    parent: BlockRef | None = None
    # ... other fields

    @model_validator(mode='before')
    @classmethod
    def handle_compact_children(cls, v: Any) -> Any:
        if isinstance(v, dict) and "children" in v:
            children = v["children"]
            if children and isinstance(children[0], list):
                v = dict(v)
                v["children"] = []
        return v

BlockEntity.model_rebuild()  # required for self-referential model
```

**Verified:** Compact `[["uuid", "val"]]` becomes `[]`; full objects parse normally.

### Pattern 5: Logging to stderr Only

MCP protocol uses stdout for JSON-RPC messages. All logging must go to stderr:

```python
# __main__.py
import logging
import sys

def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stderr,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    from logseq_mcp.server import mcp
    mcp.run()  # default transport: stdio
```

**Key:** `FastMCP.run()` defaults to `transport='stdio'`. No extra argument needed.

### Pattern 6: McpError Construction

```python
from mcp import McpError
from mcp.types import ErrorData, INTERNAL_ERROR

# Connectivity failure
raise McpError(ErrorData(
    code=INTERNAL_ERROR,
    message=f"Logseq is not running or unreachable at {url}"
))

# API error (non-retryable 4xx or exhausted retries on 5xx)
raise McpError(ErrorData(
    code=INTERNAL_ERROR,
    message=f"Logseq API error {status}: {body}"
))
```

**Verified:** `McpError` is at `mcp.McpError`; `ErrorData` and `INTERNAL_ERROR` are at `mcp.types`. There is no `mcp.exceptions` module.

### Pattern 7: Startup Token Validation

Fail fast if `LOGSEQ_API_TOKEN` is missing. Do this in `LogseqClient.__init__` or at module import, before the server accepts any connections:

```python
def __init__(self):
    self._token = os.environ.get("LOGSEQ_API_TOKEN")
    if not self._token:
        raise RuntimeError(
            "LOGSEQ_API_TOKEN environment variable is required. "
            "Set it in your MCP client config or shell environment."
        )
```

### Pattern 8: health Tool — Logseq API calls

The `health` tool needs two Logseq API calls:

```python
# Get graph name
{"method": "logseq.App.getCurrentGraph", "args": []}
# Response: {"name": "graph-name", "path": "/path/to/graph"}

# Get page count
{"method": "logseq.Editor.getAllPages", "args": []}
# Response: [{...}, {...}, ...]  (list of PageEntity objects)
```

Return format (JSON string):
```json
{"status": "ok", "graph": "graph-name", "page_count": 312}
```

### Anti-Patterns to Avoid

- **Placing Semaphore outside the client:** A module-level `asyncio.Semaphore` created at import time may be attached to the wrong event loop in Python 3.10+. Create it in `__init__`.
- **Using `mcp.run()` with explicit `transport='stdio'`:** Redundant — stdio is the default. But harmless if included.
- **Returning structured dicts from tools instead of strings:** FastMCP can handle dicts, but the tool description says return string. Stick to `str` (JSON-encoded) to avoid schema surprises.
- **Calling `BlockEntity.model_rebuild()` inside the class body:** Call it at module level after class definition.
- **Importing from `mcp.exceptions`:** This module does not exist in mcp 1.26.0. Import `McpError` from `mcp` directly.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Async context manager for httpx | Custom cleanup code | `async with httpx.AsyncClient()` inside lifespan | Built-in, handles connection pool cleanup |
| Tool registration boilerplate | Manual JSON schema generation | `@mcp.tool()` decorator | FastMCP auto-generates input schema from type hints |
| JSON-RPC framing over stdio | Custom protocol | `mcp.run()` default stdio transport | MCP SDK handles all framing, initialization, capability negotiation |
| Retry with exponential backoff | Custom loop with complex state | Simple `for attempt in range(4)` + `backoff *= 2` | Logseq needs ≤3 retries; no library needed for this simple case |

**Key insight:** The Logseq HTTP API is a simple `POST /api` RPC — no streaming, no webhooks, no auth flows. Every "clever" abstraction layer adds complexity without benefit.

---

## Common Pitfalls

### Pitfall 1: asyncio.Semaphore Created at Wrong Event Loop
**What goes wrong:** `asyncio.Semaphore(1)` created at module import time (outside any coroutine) raises `RuntimeError: no running event loop` in Python 3.10+ or silently attaches to a stale loop.
**Why it happens:** asyncio primitives must be created inside a running event loop or they use the deprecated `get_event_loop()` fallback.
**How to avoid:** Always create `asyncio.Semaphore` inside `__init__` (which is called during the lifespan, inside the event loop).
**Warning signs:** `DeprecationWarning: There is no current event loop` at import time.

### Pitfall 2: stdout Contamination Breaking MCP Protocol
**What goes wrong:** Any `print()` call, or `logging.basicConfig()` without `stream=sys.stderr`, writes to stdout. This corrupts the JSON-RPC stream and causes the MCP client to crash or silently fail.
**Why it happens:** Python's default logging stream is `sys.stderr` for `WARNING+` but many tutorials use `print()` for debugging.
**How to avoid:** Configure `logging.basicConfig(stream=sys.stderr)` before anything else in `main()`. Never use `print()` in server code.
**Warning signs:** Claude reports "unexpected token" or MCP client disconnects immediately after first tool call.

### Pitfall 3: `BlockEntity.model_rebuild()` Missing for Self-Reference
**What goes wrong:** `BlockEntity` has `children: list["BlockEntity"]` — a forward reference. Without `model_rebuild()`, Pydantic raises `PydanticUserError: `BlockEntity` is not fully defined`.
**Why it happens:** Pydantic v2 requires explicit rebuild for models with forward refs to themselves.
**How to avoid:** Call `BlockEntity.model_rebuild()` at module level in `types.py` after the class definition.
**Warning signs:** `PydanticUserError` on first model instantiation, not at import time.

### Pitfall 4: Retrying on All httpx Exceptions
**What goes wrong:** Catching `httpx.HTTPError` (the broad base class) instead of `httpx.TransportError` would catch `httpx.HTTPStatusError` (4xx/5xx responses decoded as exceptions) — mixing transport failures with application errors.
**Why it happens:** httpx exception hierarchy has two branches: `TransportError` (network-level) and `HTTPStatusError` (response-level).
**How to avoid:** Catch `httpx.TransportError` specifically for retry; check `resp.status_code` separately for 4xx/5xx decisions.
**Warning signs:** 4xx auth failures being retried 3 times instead of failing immediately.

### Pitfall 5: Logseq Returns `null` for Some Methods
**What goes wrong:** Some Logseq API methods (e.g., `getCurrentPage` when no page is open) return JSON `null`. Pydantic models or direct attribute access on the result will raise `AttributeError` or `ValidationError`.
**Why it happens:** Logseq's API is not strict about null-safety.
**How to avoid:** `_call()` should return `object` (not a typed model) and tool handlers should handle `None` explicitly.
**Warning signs:** `AttributeError: 'NoneType' object has no attribute 'name'` in health tool.

---

## Code Examples

Verified patterns from direct inspection of installed packages:

### FastMCP tool decorator with Context (mcp 1.26.0)
```python
# Source: FastMCP.tool() source + runtime verification
from mcp.server.fastmcp import FastMCP, Context

mcp = FastMCP("logseq-mcp")

@mcp.tool()
async def health(ctx: Context) -> str:
    app_ctx = ctx.request_context.lifespan_context  # returns the lifespan dataclass
    # ... call Logseq API via app_ctx.client
    return '{"status": "ok"}'
```

### McpError raise pattern (mcp 1.26.0)
```python
# Source: runtime verification
from mcp import McpError
from mcp.types import ErrorData, INTERNAL_ERROR

raise McpError(ErrorData(code=INTERNAL_ERROR, message="Logseq is not running or unreachable at http://127.0.0.1:12315"))
```

### Pydantic v2 model_validator for int-or-dict (pydantic 2.12.5)
```python
# Source: runtime verification
from pydantic import BaseModel, model_validator
from typing import Any

class BlockRef(BaseModel):
    id: int

    @model_validator(mode='before')
    @classmethod
    def coerce_int(cls, v: Any) -> Any:
        if isinstance(v, int):
            return {"id": v}
        return v
```

### pytest-asyncio test (pytest-asyncio 1.3.0)
```python
# pyproject.toml needs: [tool.pytest.ini_options] asyncio_mode = "auto"
# OR use --asyncio-mode=auto flag

import pytest
import pytest_asyncio

@pytest.mark.asyncio
async def test_client_connect_error():
    # test that McpError is raised when Logseq is not running
    ...
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `mcp.server.Server` (low-level) | `mcp.server.fastmcp.FastMCP` | mcp ~0.9 | Decorator-based tools; no manual schema; lifespan support built-in |
| `pydantic.validator` (v1) | `pydantic.model_validator(mode='before')` (v2) | pydantic 2.0 | Cleaner API; `model_rebuild()` needed for self-referential models |
| `httpx.Client` (sync) | `httpx.AsyncClient` (async) | — | Required for async tool handlers |

**Deprecated/outdated:**
- `pydantic.validator`: replaced by `field_validator` / `model_validator` in v2
- `asyncio.get_event_loop()`: deprecated in Python 3.10; use `asyncio.get_running_loop()` inside coroutines

---

## Open Questions

1. **pytest-asyncio asyncio_mode config location**
   - What we know: `asyncio_mode = "auto"` can go in `pyproject.toml` under `[tool.pytest.ini_options]`
   - What's unclear: The existing `pyproject.toml` has no `[tool.pytest.ini_options]` section yet
   - Recommendation: Add `[tool.pytest.ini_options]` with `asyncio_mode = "auto"` in pyproject.toml, or mark individual tests with `@pytest.mark.asyncio`

2. **Semaphore scope for multi-tool phases**
   - What we know: Semaphore(1) in `LogseqClient.__init__` serializes all calls through that client instance
   - What's unclear: Whether a single shared client (created in lifespan) is sufficient when multiple tools are called concurrently
   - Recommendation: Single client in lifespan is correct — all tool calls share one semaphore, which is the desired behavior

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 + pytest-asyncio 1.3.0 |
| Config file | `pyproject.toml` — `[tool.pytest.ini_options]` section (Wave 0 gap) |
| Quick run command | `uv run pytest tests/ -x -q` |
| Full suite command | `uv run pytest tests/ -v` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FOUN-01 | HTTP client sends Bearer auth header | unit | `uv run pytest tests/test_client.py::test_auth_header -x` | Wave 0 |
| FOUN-02 | Retry on TransportError + 5xx, no retry on 4xx | unit | `uv run pytest tests/test_client.py::test_retry -x` | Wave 0 |
| FOUN-03 | Semaphore serializes concurrent calls | unit | `uv run pytest tests/test_client.py::test_semaphore -x` | Wave 0 |
| FOUN-04 | Pydantic BlockRef/PageRef handle int and dict | unit | `uv run pytest tests/test_types.py -x` | Wave 0 |
| FOUN-05 | Tool registered and callable via FastMCP | unit | `uv run pytest tests/test_server.py::test_tool_registered -x` | Wave 0 |
| FOUN-06 | No output on stdout during tool call | unit | `uv run pytest tests/test_server.py::test_stderr_only -x` | Wave 0 |
| FOUN-07 | health returns graph name + page count | integration (manual) | Manual — requires live Logseq | N/A |
| FOUN-08 | httpx.AsyncClient closed after lifespan exits | unit | `uv run pytest tests/test_server.py::test_lifespan -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/ -x -q`
- **Per wave merge:** `uv run pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_client.py` — covers FOUN-01, FOUN-02, FOUN-03 (file missing; only stub existed)
- [ ] `tests/test_types.py` — covers FOUN-04
- [ ] `tests/test_server.py` — covers FOUN-05, FOUN-06, FOUN-08
- [ ] `pyproject.toml` `[tool.pytest.ini_options]` section with `asyncio_mode = "auto"`

---

## Sources

### Primary (HIGH confidence)
- Runtime inspection of mcp 1.26.0 installed at `.venv/` — FastMCP class, tool decorator, Context, lifespan pattern
- Runtime inspection of pydantic 2.12.5 — `model_validator(mode='before')`, `model_rebuild()`
- Runtime inspection of httpx 0.28.1 — `TransportError` hierarchy, `AsyncClient` API
- `graphthulhu/client/logseq.go` — retry/backoff constants (100ms, 3 retries, *2 backoff), API call pattern
- `graphthulhu/types/logseq.go` — polymorphic ref handling, BlockEntity children formats

### Secondary (MEDIUM confidence)
- `mcp/shared/context.py` source — `RequestContext.lifespan_context` field confirmed
- `mcp/server/fastmcp/server.py` source — lifespan wrapper implementation, `FastMCP.run()` signature

### Tertiary (LOW confidence)
- None — all findings verified against installed source

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all versions locked in uv.lock; patterns runtime-verified
- Architecture: HIGH — patterns compiled and executed against installed packages
- Pitfalls: HIGH — derived from source code inspection + runtime experiments
- McpError API: HIGH — runtime verified; common import path mistake documented

**Research date:** 2026-03-09
**Valid until:** 2026-06-09 (stable libraries; mcp SDK is evolving but FastMCP API stable)
