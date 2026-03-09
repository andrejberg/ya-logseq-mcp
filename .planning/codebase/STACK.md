# Technology Stack

**Analysis Date:** 2026-03-09

## Languages

**Primary:**
- Python 3.12 - All source code (`src/logseq_mcp/`), tests (`tests/`)

**Secondary:**
- None

## Runtime

**Environment:**
- CPython 3.12 (pinned in `.python-version`)
- Async runtime: anyio 4.12.1 (via MCP SDK)

**Package Manager:**
- uv (build backend: `uv_build >=0.10.4,<0.11.0`)
- Lockfile: `uv.lock` (present, 101KB)

## Frameworks

**Core:**
- MCP SDK 1.26.0 (`mcp>=1.0.0`) - Model Context Protocol server framework; provides tool registration, stdio/SSE transport, and request handling
- Pydantic 2.12.5 (`pydantic>=2.0.0`) - Data validation and type models for Logseq API entities
- httpx 0.28.1 (`httpx>=0.27.0`) - Async HTTP client for Logseq API communication

**Testing:**
- pytest 9.0.2 (`pytest>=8.0.0`) - Test runner
- pytest-asyncio 1.3.0 (`pytest-asyncio>=0.24.0`) - Async test support for `async def` tool handlers

**Build/Dev:**
- uv_build 0.10.4+ - PEP 517 build backend (declared in `pyproject.toml` `[build-system]`)

## Key Dependencies

**Critical (direct):**
- `mcp` 1.26.0 - The MCP server framework; defines the entire server interface. Brings in starlette, uvicorn, sse-starlette, pydantic-settings, pyjwt
- `httpx` 0.28.1 - Async HTTP client used in `client.py` for all Logseq API calls
- `pydantic` 2.12.5 - Models in `types.py` for `PageEntity`, `BlockEntity`, `PageRef`, `BlockRef`

**Infrastructure (transitive via MCP SDK):**
- starlette 0.52.1 - ASGI framework (SSE transport)
- uvicorn 0.41.0 - ASGI server (SSE transport)
- sse-starlette 3.3.2 - Server-Sent Events support
- anyio 4.12.1 - Async compatibility layer
- pydantic-settings - Environment variable configuration
- pyjwt[crypto] - JWT auth support (MCP auth layer)

## Configuration

**Environment:**
- `LOGSEQ_API_URL` - Logseq HTTP API endpoint (default: `http://127.0.0.1:12315`)
- `LOGSEQ_API_TOKEN` - Bearer token for Logseq API authentication (required)
- `.env` file supported (listed in `.gitignore`)

**Build:**
- `pyproject.toml` - Single project configuration file (PEP 621 metadata + uv build system)
- `.python-version` - Pins Python 3.12

## Entry Points

**CLI script:**
- `logseq-mcp` console script mapped to `logseq_mcp.__main__:main` (declared in `[project.scripts]`)
- Also runnable as `uv run python -m logseq_mcp`

## Platform Requirements

**Development:**
- Python >= 3.12
- uv package manager
- Logseq desktop app running with HTTP API enabled on port 12315

**Production:**
- Same as development (local MCP server, not deployed to cloud)
- Runs as stdio or SSE transport alongside Claude Code

---

*Stack analysis: 2026-03-09*
