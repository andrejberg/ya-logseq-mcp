# External Integrations

**Analysis Date:** 2026-03-09

## APIs & External Services

**Logseq HTTP API (primary and only external integration):**
- Purpose: All graph read/write operations (pages, blocks, queries, templates)
- Protocol: HTTP POST to single endpoint `http://127.0.0.1:12315/api`
- Request format: `{"method": "logseq.Editor.*|logseq.DB.*|logseq.App.*", "args": [...]}`
- Auth: Bearer token via `Authorization` header
- SDK/Client: Custom async client in `src/logseq_mcp/client.py` using `httpx.AsyncClient`
- Connection: Localhost only (Logseq desktop app must be running)

**Logseq API Methods Used:**

| Namespace | Method | Purpose |
|-----------|--------|---------|
| `logseq.Editor` | `getAllPages` | List all pages |
| `logseq.Editor` | `getPage` | Get single page by name/id |
| `logseq.Editor` | `getPageBlocksTree` | Get block tree for a page |
| `logseq.Editor` | `getPageLinkedReferences` | Get backlinks to a page |
| `logseq.Editor` | `getBlock` | Get single block by UUID |
| `logseq.Editor` | `appendBlockInPage` | Append block to page |
| `logseq.Editor` | `insertBlock` | Insert block at position |
| `logseq.Editor` | `updateBlock` | Update block content |
| `logseq.Editor` | `removeBlock` | Delete block |
| `logseq.Editor` | `moveBlock` | Move block to new location |
| `logseq.Editor` | `createPage` | Create new page |
| `logseq.Editor` | `deletePage` | Delete page |
| `logseq.Editor` | `renamePage` | Rename page (auto-updates links) |
| `logseq.DB` | `datascriptQuery` | Raw DataScript queries |
| `logseq.App` | `getCurrentGraphTemplates` | List templates |
| `logseq.App` | `getTemplate` | Get template content |
| `logseq.App` | `createTemplate` | Create template |
| `logseq.App` | `removeTemplate` | Delete template |
| `logseq.App` | `insertTemplate` | Apply template |
| `logseq.App` | `getCurrentGraph` | Get graph name (health check) |

## MCP Protocol (upstream consumer)

**Claude Code / MCP Client:**
- This server exposes 27 tools via the Model Context Protocol
- Transport: stdio (primary) or SSE (via uvicorn/starlette)
- Configuration: Added to `~/.claude/.mcp.json` as a server entry
- The MCP SDK handles all protocol framing, tool schema generation, and request routing

## Data Storage

**Databases:**
- None directly. All data lives in Logseq's local graph (markdown files on disk managed by Logseq)
- Logseq exposes a DataScript (Datalog) query interface via `logseq.DB.datascriptQuery`

**File Storage:**
- No direct file I/O. All graph access is through the HTTP API

**Caching:**
- None

## Authentication & Identity

**Logseq API Auth:**
- Bearer token authentication
- Token source: `LOGSEQ_API_TOKEN` environment variable
- Token is set in Logseq desktop app settings (API > Authorization token)
- No OAuth, no refresh — static token for local communication

**MCP Auth:**
- MCP SDK includes pyjwt[crypto] for JWT-based auth, but this server uses stdio transport (no auth needed for local pipe)

## Monitoring & Observability

**Error Tracking:**
- None (local tool, no remote error reporting)

**Logs:**
- Python standard logging (via MCP SDK defaults)
- `health` tool provides basic connectivity verification (pings Logseq, returns graph name + page count)

## CI/CD & Deployment

**Hosting:**
- Local only. Runs as a subprocess of Claude Code on the developer's machine

**CI Pipeline:**
- None configured

**Deployment:**
- `uv run python -m logseq_mcp` or via `logseq-mcp` console script
- Registered in `~/.claude/.mcp.json` for Claude Code to discover and launch

## Environment Configuration

**Required env vars:**
- `LOGSEQ_API_TOKEN` - Bearer token for Logseq API (no default, must be set)

**Optional env vars:**
- `LOGSEQ_API_URL` - API endpoint (default: `http://127.0.0.1:12315`)

**Secrets location:**
- `.env` file in project root (gitignored)
- Workspace-level `.env` at `~/Workspace/.env`

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None

## External Dependencies at Runtime

**Logseq Desktop App:**
- Must be running with HTTP API server enabled
- API server listens on `http://127.0.0.1:12315` by default
- Graph must be open (the API operates on the currently active graph)
- If Logseq is not running or API is disabled, all tools fail with connection errors

## Reference Implementation

**graphthulhu (Go):**
- Located at `graphthulhu/` in this repo (gitignored, reference only)
- The predecessor MCP server being replaced
- Key reference files for API patterns:
  - `graphthulhu/client/logseq.go` - HTTP client patterns
  - `graphthulhu/types/logseq.go` - Data model structures
  - `graphthulhu/tools/navigate.go` - Read tool implementations
  - `graphthulhu/tools/search.go` - DataScript query patterns
  - `graphthulhu/tools/write.go` - Write tool implementations
  - `graphthulhu/tools/journal.go` - Journal date format handling
  - `graphthulhu/server.go` - Tool registration pattern

---

*Integration audit: 2026-03-09*
