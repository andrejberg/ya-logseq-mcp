# CLAUDE.md — logseq-mcp

## Project Identity
- **Slug**: `logseq-mcp`
- **Purpose**: Custom Python MCP server for Logseq — replaces graphthulhu with a focused, Logseq-only implementation tailored to this workspace's conventions.
- **Type**: `tool`
- **Status**: planning

## Workspace Relationship
- **Logseq project page**: `[[Logseq MCP]]` (to be created)
- **Workspace root**: `~/Workspace/`
- **Disk path**: `~/Workspace/projects/logseq-mcp/`

## Why This Exists

Forked graphthulhu MCP had three confirmed problems:
1. **Block duplication bug** — `get_page` returns blocks 4-8× due to recursive traversal bug; skills can't fix bad data
2. **Verbosity** — full enrichment on every read, no lean path; `compact: true` doesn't fix duplication
3. **Dead weight** — ~40% of graphthulhu is Obsidian/flashcard/whiteboard code that is never used; it's opaque and unmaintainable in Go

**Language choice: Python over Go** — Logseq HTTP API is simple `POST /api` RPC; performance is API-bound not language-bound. Python fits the workspace toolchain (`uv`) and is maintainable without Go knowledge.

## Environment
- **Tool**: `uv`
- **Python**: ≥3.12
- **Key deps**: `mcp`, `httpx`, `pydantic`
- **Async**: All tool handlers are `async def`; uses `httpx.AsyncClient`

## Layout

Current v1 layout in this repo:
```
projects/logseq-mcp/
├── CLAUDE.md               ← this file
├── pyproject.toml          ← uv project
├── src/
│   └── logseq_mcp/
│       ├── __init__.py
│       ├── __main__.py     ← entry point: `python -m logseq_mcp`
│       ├── server.py       ← MCP server + tool registration
│       ├── client.py       ← Logseq HTTP client (async, retry, auth)
│       ├── types.py        ← Pydantic models for API entities
│       └── tools/
│           ├── __init__.py
│           ├── core.py     ← current v1 read tools
│           └── write.py    ← current v1 write tools
└── tests/                  ← unit and integration tests
```

## Current v1 Tool Scope (9 tools)

This is the active roadmap scope for the current release. Anything beyond this is deferred unless `.planning/REQUIREMENTS.md` and `.planning/ROADMAP.md` are updated.

### Core Reads (4)
- `get_page` — page + block tree, **deduped by UUID**, lean by default
- `get_block` — single block by UUID with optional children
- `list_pages` — pages with optional namespace filter
- `get_references` — backlinks to a page (via `getPageLinkedReferences`)

### Write (4)
- `page_create` — create page with properties + initial blocks
- `block_append` — append blocks to a page; accepts flat strings or nested `{content, properties, children}` objects
- `block_update` — update block content by UUID
- `block_delete` — delete block by UUID

### Utility (1)
- `health` — ping Logseq, return graph name + page count

## Deferred Tool Surface

These tool families are intentional future ideas, not current execution scope:
- Query: `query`, `find_by_tag`, `query_properties`
- Journal: `journal_today`, `journal_append`, `journal_range`
- Kanban: `kanban_get`, `kanban_move`, `kanban_add_task`, `kanban_list`
- Templates: `template_list`, `template_get`, `template_create`, `template_delete`, `template_apply`
- Additional writes: `delete_page`, `rename_page`, `move_block`

## Logseq HTTP API
All operations are `POST http://127.0.0.1:12315/api` with `{"method": "...", "args": [...]}`.
Auth: `Bearer <token>` from env `LOGSEQ_API_TOKEN`.

Methods used:
```
# Editor
logseq.Editor.getAllPages
logseq.Editor.getPage
logseq.Editor.getPageBlocksTree
logseq.Editor.getPageLinkedReferences
logseq.Editor.getBlock
logseq.Editor.appendBlockInPage
logseq.Editor.insertBlock
logseq.Editor.updateBlock
logseq.Editor.removeBlock
logseq.Editor.createPage
logseq.App.getCurrentGraph
```

Deferred/post-v1 API methods remain out of current execution scope until the roadmap changes:
- `logseq.DB.datascriptQuery`
- `logseq.Editor.moveBlock`
- `logseq.Editor.deletePage`
- `logseq.Editor.renamePage`
- `logseq.App.getCurrentGraphTemplates`
- `logseq.App.getTemplate`
- `logseq.App.createTemplate`
- `logseq.App.removeTemplate`
- `logseq.App.insertTemplate`

## Key Design Decisions

| Problem in graphthulhu | Solution here |
|------------------------|---------------|
| Block duplication bug | Deduplicate by UUID at read time in `get_page` |
| Always-verbose enrichment | Lean by default; no parsed links/tags/ancestors unless requested |
| Brute-force search (scan all pages) | Not part of v1; current scope stays narrow and read/write focused |
| Obsidian backend | Removed entirely |
| Flashcard/whiteboard/decision tools | Not implemented |
| Two block-append tools (flat + nested) | Single `block_append` handles both flat strings and nested objects |
| Sync HTTP client | Async throughout: `httpx.AsyncClient` + async tool handlers |

### Types (`types.py`)
Pydantic models mirroring graphthulhu's types:
- `PageEntity`: id, uuid, name, original_name, journal, journal_day, properties, namespace
- `BlockEntity`: id, uuid, content, format, marker, priority, page, parent, left, children, properties, refs, path_refs, pre_block
- `PageRef`, `BlockRef` — handle both `{"id": N}` and plain `N` formats via Pydantic validators

## Deferred Feature Notes

The following notes are retained only as future reference and are not authoritative for the current v1 release:
- DataScript query patterns for `query`, `find_by_tag`, and `query_properties`
- Journal date-format handling ideas
- Kanban column conventions and task property schema
- Template CRUD and apply behavior

## Configuration
```
LOGSEQ_API_URL=http://127.0.0.1:12315   (default)
LOGSEQ_API_TOKEN=<token>                (required)
```

For live integration work in Phase 4 and later, load the shared test credentials before running pytest or MCP smoke commands:

```bash
source ~/Workspace/.env
```

This repo expects that file to provide the Logseq live-test environment, including `LOGSEQ_API_TOKEN`. Keep `LOGSEQ_TEST_GRAPH_NAME=logseq-test-graph` unless a plan explicitly says otherwise.

Run:
```bash
uv run python -m logseq_mcp
```

## Implementation Phases

For the current v1 roadmap, phase sequencing is defined by `.planning/ROADMAP.md` and `.planning/REQUIREMENTS.md`. That v1 sequence is:

### Phase 1: Foundation
1. `pyproject.toml` — project setup with deps
2. `types.py` — Pydantic models
3. `client.py` — async Logseq HTTP client
4. `server.py` + `__main__.py` — MCP server skeleton
5. `health` tool — verify end-to-end connectivity

### Phase 2: Core Reads
6. `get_page` (with deduplication fix)
7. `get_block`
8. `list_pages`
9. `get_references`

### Phase 3: Write Tools
10. `page_create`
11. `block_append` (flat + nested)
12. `block_update`
13. `block_delete`

### Phase 4: Integration and Swap
14. Isolated test graph and live integration harness
15. Black-box MCP stdio verification
16. Graphthulhu parity on a fixed fixture page
17. Claude MCP config swap with rollback path

Post-v1 ideas remain deferred and are not part of the current roadmap execution order:
- Query expansion: `query`, `find_by_tag`, `query_properties`
- Journal: `journal_today`, `journal_append`, `journal_range`
- Templates: `template_list`, `template_get`, `template_create`, `template_delete`, `template_apply`
- Kanban: `kanban_get`, `kanban_move`, `kanban_add_task`, `kanban_list`
- Additional writes: `delete_page`, `rename_page`, `move_block`

## Migration Path
1. Build and test against live Logseq using the isolated Phase 4 graph first
2. Verify parity on Phase 4's fixed `get_page` fixture while graphthulhu remains available
3. Swap `.mcp.json` to point to the new server, then run isolated-graph and read-only daily-driver smoke checks
4. Keep graphthulhu repo as reference — do not delete

## Git
- **This repo**: `yes` — independent git repo
- **Remote**: none
- **Branch strategy**: `main` only

## Automation Contract

### Claude may change
- All `src/` files
- `tests/`
- `pyproject.toml`
- `CLAUDE.md` itself

### Never change automatically
- Nothing sensitive — no credentials committed

## Reference Files
- `graphthulhu/client/logseq.go` — API call patterns to replicate
- `graphthulhu/types/logseq.go` — data model to replicate in Pydantic
- `graphthulhu/tools/navigate.go` — get_page, get_block, list_pages, get_links logic
- `graphthulhu/tools/search.go` — DataScript query patterns for find_by_tag, query_properties
- `graphthulhu/tools/write.go` — write tool implementations
- `graphthulhu/tools/journal.go` — journal date format handling
- `graphthulhu/server.go` — tool registration pattern
