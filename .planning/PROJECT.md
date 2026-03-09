# Logseq MCP Server

## What This Is

A custom Python MCP server for Logseq that replaces graphthulhu — a Go-based MCP server with unpredictable behavior. This is a from-scratch rewrite focused on correct Logseq block structure, lean output, and full maintainability. Built for one user's workspace workflow.

## Core Value

Every read returns correctly structured blocks and every write produces valid Logseq content — no duplicates, no ghost blocks, no broken hierarchy.

## Requirements

### Validated

<!-- Shipped and confirmed valuable. -->

(None yet — ship to validate)

### Active

<!-- Current scope. Building toward these. -->

- [ ] Async HTTP client talks to Logseq API with retry and auth
- [ ] `get_page` returns deduplicated block tree with correct parent/child nesting
- [ ] `get_block` returns a single block by UUID with optional children
- [ ] `list_pages` returns pages with optional namespace/tag/property filter
- [ ] `get_references` returns backlinks to a page
- [ ] `find_by_tag` finds blocks/pages by tag via DataScript
- [ ] `query_properties` finds blocks/pages by property key/value via DataScript
- [ ] `query` passes raw DataScript queries through
- [ ] `page_create` creates a page with properties and initial blocks
- [ ] `block_append` appends blocks (flat strings or nested objects) with correct indentation
- [ ] `block_update` updates block content by UUID
- [ ] `block_delete` deletes a block by UUID
- [ ] `delete_page` deletes a page entirely
- [ ] `rename_page` renames a page (Logseq updates links)
- [ ] `move_block` moves a block to a new location
- [ ] `journal_today` gets or creates today's journal page
- [ ] `journal_append` appends blocks to a journal page by date
- [ ] `journal_range` fetches journal entries for a date range
- [ ] `health` tool verifies connectivity and returns graph info
- [ ] Integration tests run against a local test graph (isolated from real graph)

### Out of Scope

<!-- Explicit boundaries. Includes reasoning to prevent re-adding. -->

- Kanban tools (kanban_get, kanban_move, kanban_add_task, kanban_list) — not daily-driver; add in v2
- Template tools (template_list, template_get, template_create, template_delete, template_apply) — not daily-driver; add in v2
- Obsidian backend — removed entirely, Logseq-only
- Flashcard/whiteboard/decision tools — never used
- Content parsing (extracting links/tags from block content) — lean output by design
- In-memory graph analysis — not needed; Logseq is source of truth
- Search tool (brute-force page scanning) — use DataScript queries instead

## Context

- Scaffolding already exists: `pyproject.toml`, `src/logseq_mcp/` package structure, `types.py`, `client.py`, `server.py`, `__main__.py`, and tool module stubs
- graphthulhu source is available as reference at `graphthulhu/` in the workspace
- Logseq HTTP API is `POST http://127.0.0.1:12315/api` with JSON-RPC style `{"method": "...", "args": [...]}`
- API always targets whichever graph is open in Logseq desktop app — no graph selection
- Testing will use a dedicated Logseq graph inside the project directory for isolation
- The key formatting bugs in graphthulhu: wrong indentation, broken heading hierarchy, ghost empty blocks, blocks Logseq couldn't render

## Constraints

- **Tech stack**: Python ≥3.12, uv, httpx (async), Pydantic, MCP SDK — already chosen and scaffolded
- **API dependency**: Logseq desktop must be running with HTTP API enabled on port 12315
- **No local state**: Server is stateless; Logseq is the single source of truth
- **Block structure**: Writes must produce valid Logseq hierarchy — correct parent/child nesting is non-negotiable

## Key Decisions

<!-- Decisions that constrain future work. Add throughout project lifecycle. -->

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Python over Go | Maintainability — can debug and adapt; API is HTTP-bound not CPU-bound | — Pending |
| Lean output by default | graphthulhu's verbose enrichment was unnecessary; keep responses minimal | — Pending |
| Deduplicate by UUID | Fix graphthulhu's 4-8x block duplication bug at read time | — Pending |
| Local test graph for integration tests | API targets open graph; isolated test graph keeps real data safe | — Pending |
| Core + Write + Journal first | Daily-driver tools define swap threshold; kanban/templates are v2 | — Pending |

---
*Last updated: 2026-03-09 after initialization*
