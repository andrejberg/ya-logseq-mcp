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
│           ├── core.py     ← get_page, get_block, list_pages, get_references, find_by_tag, query_properties, query
│           ├── journal.py  ← journal_today, journal_append, journal_range
│           ├── kanban.py   ← kanban_get, kanban_move, kanban_add_task, kanban_list
│           ├── templates.py ← template_list, template_get, template_create, template_delete, template_apply
│           └── write.py    ← page_create, block_append, block_update, block_delete, delete_page, rename_page, move_block
└── tests/
    └── test_client.py
```

## Tools (27 total)

### Core Reads (6)
- `get_page` — page + block tree, **deduped by UUID**, lean by default
- `get_block` — single block by UUID with optional children
- `list_pages` — pages with optional namespace/tag/property filter
- `get_references` — backlinks to a page (via `getPageLinkedReferences`)
- `find_by_tag` — find blocks/pages by tag via DataScript
- `query_properties` — find blocks/pages by property key/value via DataScript

### Query (1)
- `query` — raw DataScript passthrough

### Journal (3)
- `journal_today` — get or create today's journal page
- `journal_append` — append blocks to a journal page (by date string or "today")
- `journal_range` — fetch journal entries for a date range

### Kanban (4)
- `kanban_get` — board page with tasks per column, deduped and flat
- `kanban_move` — move task block to a column (knows the 4 standard columns by name)
- `kanban_add_task` — create task with this workspace's property schema
- `kanban_list` — list tasks by column/project/status

### Write (7)
- `page_create` — create page with properties + initial blocks
- `block_append` — append blocks to a page; accepts flat strings or nested `{content, properties, children}` objects
- `block_update` — update block content by UUID
- `block_delete` — delete block by UUID
- `delete_page` — delete page entirely
- `rename_page` — rename page; Logseq updates links automatically
- `move_block` — move block to new location (before, after, or as child)

### Templates (5)
- `template_list` — list all templates in the graph
- `template_get` — get a template's content by name
- `template_create` — create a template from an existing block
- `template_delete` — delete a template by name
- `template_apply` — insert template at a page or block

### Utility (1)
- `health` — ping Logseq, return graph name + page count

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
logseq.Editor.moveBlock
logseq.Editor.createPage
logseq.Editor.deletePage
logseq.Editor.renamePage

# DB
logseq.DB.datascriptQuery

# App (templates)
logseq.App.getCurrentGraphTemplates
logseq.App.getTemplate
logseq.App.createTemplate
logseq.App.removeTemplate
logseq.App.insertTemplate
logseq.App.getCurrentGraph
```

## Key Design Decisions

| Problem in graphthulhu | Solution here |
|------------------------|---------------|
| Block duplication bug | Deduplicate by UUID at read time in `get_page` |
| Always-verbose enrichment | Lean by default; no parsed links/tags/ancestors unless requested |
| Brute-force search (scan all pages) | No search tool; use `query` (DataScript), `find_by_tag`, `query_properties` instead |
| Generic `move_block` | `kanban_move` knows the 4 column names; generic `move_block` also available |
| Journal date format guessing | Try multiple formats: `"Mar 8th, 2026"`, `"March 8th, 2026"`, `"2026-03-08"`, `"March 8, 2026"` |
| Generic task properties | Knows workspace schema: `type::`, `project::`, `effort::`, `dod::`, etc. |
| No template support | Full template CRUD + apply via `App.*` API methods |
| Obsidian backend | Removed entirely |
| Flashcard/whiteboard/decision tools | Not implemented |
| Two block-append tools (flat + nested) | Single `block_append` handles both flat strings and nested objects |
| Sync HTTP client | Async throughout: `httpx.AsyncClient` + async tool handlers |

### Types (`types.py`)
Pydantic models mirroring graphthulhu's types:
- `PageEntity`: id, uuid, name, original_name, journal, journal_day, properties, namespace
- `BlockEntity`: id, uuid, content, format, marker, priority, page, parent, left, children, properties, refs, path_refs, pre_block
- `PageRef`, `BlockRef` — handle both `{"id": N}` and plain `N` formats via Pydantic validators

### DataScript query patterns
Reuse graphthulhu's proven queries:
```clojure
;; find_by_tag
[:find (pull ?b [:block/uuid :block/content {:block/page [:block/name :block/original-name]}])
 :where [?b :block/refs ?ref] [?ref :block/name "tag-name"]]

;; query_properties (with value)
[:find (pull ?b [:block/uuid :block/content :block/properties {:block/page [:block/name :block/original-name]}])
 :where [?b :block/properties ?props] [(get ?props :prop-name) ?v] [(str ?v) ?vs] [(clojure.string/includes? ?vs "value")]]
```

## Kanban Column Convention
Standard columns (must match exactly in Logseq):
- `BACKLOG`
- `SPRINT BACKLOG`
- `IN PROGRESS`
- `FINISHED`

## Task Property Schema
Required properties for tasks:
```
type:: Task
project:: <slug>
task_type:: <dev|research|documentation|infra>
execution_type:: <automated|semi-automated|manual>
effort:: <1-13>
description:: <what>
dod:: <done criteria>
assignee::
```

## Configuration
```
LOGSEQ_API_URL=http://127.0.0.1:12315   (default)
LOGSEQ_API_TOKEN=<token>                (required)
```

Run:
```bash
uv run python -m logseq_mcp
```

## Implementation Phases

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
10. `query` (raw DataScript)
11. `find_by_tag`
12. `query_properties`

### Phase 3: Write Tools
13. `page_create`
14. `block_append` (flat + nested)
15. `block_update`
16. `block_delete`
17. `delete_page`
18. `rename_page`
19. `move_block`

### Phase 4: Journal
20. `journal_today`
21. `journal_append`
22. `journal_range`

### Phase 5: Templates
23. `template_list`
24. `template_get`
25. `template_create`
26. `template_delete`
27. `template_apply`

### Phase 6: Kanban
28. `kanban_get`
29. `kanban_move`
30. `kanban_add_task`
31. `kanban_list`

### Phase 7: Integration
32. Add to `~/.claude/.mcp.json` alongside graphthulhu
33. Verify parity on key tools
34. Swap — remove graphthulhu entry

## Migration Path
1. Build and test against live Logseq (both MCPs active in `.mcp.json`)
2. Verify parity on key tools: `get_page`, `kanban_get`, `journal_today`
3. Swap `.mcp.json` to point to new server; remove graphthulhu entry
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
