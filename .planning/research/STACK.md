# Technology Stack

**Project:** logseq-mcp
**Researched:** 2026-03-09

## Recommended Stack

### Core Framework

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| MCP Python SDK (`mcp`) | 1.26.0 (locked) | MCP server framework | Official SDK; `FastMCP` class provides decorator-based tool registration with automatic JSON Schema generation from type hints. Already locked in `uv.lock`. | HIGH |
| httpx | 0.28.1 (locked) | Async HTTP client | `AsyncClient` with connection pooling for all Logseq API calls. Only real async HTTP client in Python. Already locked. | HIGH |
| Pydantic | 2.12.5 (locked) | Data validation/models | Models for `PageEntity`, `BlockEntity`, etc. Handles Logseq's inconsistent response shapes (e.g., `{"id": N}` vs plain `N`) via `model_validator(mode='before')`. Already locked. | HIGH |

### Testing

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| pytest | 9.0.2 (locked) | Test runner | Standard. Already locked. | HIGH |
| pytest-asyncio | 1.3.0 (locked) | Async test support | Required for testing `async def` tool handlers and the httpx client. Use `auto` mode (`asyncio_mode = "auto"` in `pyproject.toml`) to avoid decorating every test with `@pytest.mark.asyncio`. Already locked. | HIGH |

### Infrastructure (transitive, via MCP SDK)

| Technology | Version | Purpose | Notes |
|------------|---------|---------|-------|
| anyio | 4.12.1 | Async runtime abstraction | MCP SDK's async layer; do not import directly -- use `asyncio` stdlib |
| starlette | 0.52.1 | ASGI framework | SSE transport only; not relevant for stdio mode |
| uvicorn | 0.41.0 | ASGI server | SSE transport only; not relevant for stdio mode |
| pydantic-settings | (transitive) | Env var config | Available via MCP but not needed; use simple `os.environ.get()` for two config vars |

## Key Design Decisions

### Use FastMCP, not low-level Server

**Decision:** Use `mcp.server.fastmcp.FastMCP` for tool registration.

**Why:** FastMCP generates JSON Schema from Python type hints and docstrings automatically. Tool functions are plain `async def` with type-annotated parameters. No manual schema writing. The MCP SDK docs recommend FastMCP as the primary interface, with low-level `Server` only for advanced protocol customization this project does not need.

**Pattern:**
```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("logseq-mcp")

@mcp.tool()
async def get_page(name: str, include_children: bool = True) -> dict:
    """Get a page and its block tree from Logseq."""
    ...
```

**Confidence:** HIGH -- FastMCP is the official recommended pattern in MCP SDK 1.26.0.

### Use stdio transport, not SSE

**Decision:** Run as stdio transport (`mcp.run(transport="stdio")`).

**Why:** Claude Code connects to MCP servers via stdio. SSE transport is for web-based clients. Stdio is simpler (no port binding, no auth layer) and matches how `~/.claude/.mcp.json` invokes servers.

**Confidence:** HIGH -- this is how graphthulhu runs today.

### Hand-roll retry logic, skip tenacity

**Decision:** Implement retry as a simple loop in `client.py` instead of adding `tenacity` as a dependency.

**Why:** The retry surface is tiny -- one method (`LogseqClient._call`) talking to one local endpoint. A 3-line retry loop with exponential backoff is clearer than a decorator from a 9.x library. Fewer dependencies = fewer breakage vectors for a tool that must always work.

**Pattern:**
```python
async def _call(self, method: str, args: list) -> Any:
    last_error = None
    for attempt in range(self.max_retries):
        try:
            response = await self._client.post(...)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            last_error = e
            if attempt < self.max_retries - 1:
                await asyncio.sleep(0.5 * (2 ** attempt))
    raise last_error
```

**Confidence:** HIGH -- single-endpoint local API does not need a retry framework.

### Pydantic `model_validator(mode='before')` for Logseq's inconsistent shapes

**Decision:** Use `@model_validator(mode='before')` on `PageRef` and `BlockRef` to normalize Logseq's inconsistent response format (sometimes `{"id": 123}`, sometimes bare `123`).

**Why:** Logseq's HTTP API does not return consistent shapes. Pre-validators let us normalize before Pydantic's field validation runs. This is cleaner than `Union[int, dict]` fields with post-processing.

**Pattern:**
```python
class PageRef(BaseModel):
    id: int

    @model_validator(mode='before')
    @classmethod
    def normalize(cls, data: Any) -> dict:
        if isinstance(data, int):
            return {"id": data}
        return data
```

**Confidence:** HIGH -- confirmed Pydantic v2 pattern.

### pytest-asyncio in auto mode

**Decision:** Set `asyncio_mode = "auto"` in `pyproject.toml`.

**Why:** Every test in this project will be async (testing async tool handlers and the async HTTP client). Auto mode eliminates the need for `@pytest.mark.asyncio` on every test function. This project uses asyncio exclusively (no trio/anyio).

**Config:**
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

**Confidence:** HIGH -- pytest-asyncio 1.3.0 stable feature.

## What NOT to Use

| Technology | Why Not |
|------------|---------|
| `fastmcp` (PyPI package, separate from SDK) | Separate project from PrefectHQ. The MCP SDK already includes `FastMCP` at `mcp.server.fastmcp`. Adding the separate `fastmcp` package would create confusion and version conflicts. |
| `tenacity` | Overkill for one retry point against localhost. Hand-rolled 3-line loop is clearer. |
| `pydantic-settings` | Only two env vars (`LOGSEQ_API_URL`, `LOGSEQ_API_TOKEN`). `os.environ.get()` with defaults is simpler than a Settings class. |
| `aiohttp` | httpx is already locked and is the modern standard. aiohttp has a more complex API and is unnecessary. |
| `requests` | Synchronous. This project is async throughout. |
| `respx` | HTTP mocking library for httpx. Not needed -- integration tests hit real Logseq API against a test graph. Unit tests can mock the client directly with `unittest.mock.AsyncMock`. |
| `click` / `typer` | No CLI arguments needed. Entry point is `mcp.run()` with stdio transport. |

## Alternatives Considered

| Category | Recommended | Alternative | Why Not Alternative |
|----------|-------------|-------------|---------------------|
| MCP API | `FastMCP` (in SDK) | Low-level `Server` class | Manual schema writing, no benefit for this use case |
| HTTP Client | `httpx` | `aiohttp` | httpx already locked; simpler API; aiohttp adds complexity |
| Retry | Hand-rolled | `tenacity` | One retry point, not worth a dependency |
| Config | `os.environ` | `pydantic-settings` | Two variables, not worth a framework |
| Test mocking | `unittest.mock.AsyncMock` | `respx` | Integration tests hit real API; unit tests mock at client level |
| Transport | stdio | SSE / Streamable HTTP | Claude Code uses stdio; SSE adds unnecessary complexity |

## Dependency Changes Needed

The current `pyproject.toml` dependencies are correct and sufficient:

```toml
dependencies = [
    "mcp>=1.0.0",
    "httpx>=0.27.0",
    "pydantic>=2.0.0",
]

[dependency-groups]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
]
```

**No new dependencies required.** The locked versions (mcp 1.26.0, httpx 0.28.1, pydantic 2.12.5, pytest 9.0.2, pytest-asyncio 1.3.0) are all current as of March 2026.

**One config addition needed:**

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

## Version Currency Check

| Package | Locked | Latest on PyPI | Status |
|---------|--------|----------------|--------|
| mcp | 1.26.0 | 1.26.0 | Current |
| httpx | 0.28.1 | 0.28.1 | Current |
| pydantic | 2.12.5 | 2.12.5 | Current |
| pytest | 9.0.2 | 9.0.2 | Current |
| pytest-asyncio | 1.3.0 | 1.3.0 | Current |

All locked versions match latest stable releases. No updates needed.

## Sources

- [MCP Python SDK - GitHub](https://github.com/modelcontextprotocol/python-sdk) -- official SDK repo
- [MCP Python SDK - Docs](https://py.sdk.modelcontextprotocol.io/) -- official documentation
- [MCP Python SDK - PyPI](https://pypi.org/project/mcp/) -- version 1.26.0, released 2026-01-24
- [Build an MCP Server - Official Guide](https://modelcontextprotocol.io/docs/develop/build-server) -- FastMCP patterns
- [httpx Async Support](https://www.python-httpx.org/async/) -- AsyncClient patterns
- [httpx Clients - Advanced](https://www.python-httpx.org/advanced/clients/) -- connection pooling
- [Pydantic Validators](https://docs.pydantic.dev/latest/concepts/validators/) -- model_validator patterns
- [pytest-asyncio Concepts](https://pytest-asyncio.readthedocs.io/en/stable/concepts.html) -- auto mode docs
- [httpx - PyPI](https://pypi.org/project/httpx/) -- version 0.28.1
- [pydantic - PyPI](https://pypi.org/project/pydantic/) -- version 2.12.5
- [pytest-asyncio - PyPI](https://pypi.org/project/pytest-asyncio/) -- version 1.3.0
