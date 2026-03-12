# Logseq MCP Server

## What This Is

A custom Python MCP server for Logseq that has now shipped as the replacement path for graphthulhu in this workspace. It is a from-scratch rewrite focused on correct Logseq block structure, lean output, maintainability, and safe daily-driver rollout.

## Core Value

Every read returns correctly structured blocks and every write produces valid Logseq content — no duplicates, no ghost blocks, no broken hierarchy.

## Requirements

### Validated

- ✓ Async HTTP client talks to Logseq API with retry/auth and single-flight request serialization — v1.0
- ✓ `health` verifies live Logseq connectivity over the production MCP server entrypoint — v1.0
- ✓ `get_page` returns deduplicated block trees with correct parent/child nesting — v1.0
- ✓ `get_block`, `list_pages`, and `get_references` cover the core daily-driver read surface — v1.0
- ✓ `page_create`, `block_append`, `block_update`, and `block_delete` produce valid Logseq content and verify mutations through follow-up reads — v1.0
- ✓ Integration coverage runs against an isolated graph and proves parity against graphthulhu on the fixed fixture page — v1.0

### Active

- [ ] `find_by_tag` finds blocks/pages by tag via DataScript
- [ ] `query_properties` finds blocks/pages by property key/value via DataScript
- [ ] `query` passes raw DataScript queries through
- [ ] `delete_page` deletes a page entirely
- [ ] `rename_page` renames a page (Logseq updates links)
- [ ] `move_block` moves a block to a new location
- [ ] `journal_today` gets or creates today's journal page
- [ ] `journal_append` appends blocks to a journal page by date
- [ ] `journal_range` fetches journal entries for a date range

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
| Python over Go | Maintainability — can debug and adapt; API is HTTP-bound not CPU-bound | ✓ Good |
| Lean output by default | graphthulhu's verbose enrichment was unnecessary; keep responses minimal | ✓ Good |
| Deduplicate by UUID | Fix graphthulhu's 4-8x block duplication bug at read time | ✓ Good |
| Local test graph for integration tests | API targets open graph; isolated test graph keeps real data safe | ✓ Good |
| Core + Write + Journal first | Daily-driver tools define swap threshold; kanban/templates are v2 | ⚠ Revisit |

## Current State

- Shipped milestone: `v1.0` on 2026-03-12
- Delivered surface: `health`, `get_page`, `get_block`, `list_pages`, `get_references`, `page_create`, `block_append`, `block_update`, `block_delete`
- Validation state: isolated live graph, MCP stdio transport, and structural graphthulhu parity are all complete
- Rollout state: `logseq-mcp` passed the shared-config smoke gate while graphthulhu remains available as fallback
- Known archive debt: milestone audit is `tech_debt` because the Phase 1 live-health evidence trail and Phases 1/3 Nyquist cleanup remain partial

## Next Milestone Goals

- Turn the deferred query, journal, and additional write tools into a scoped next milestone rather than broad backlog carry-over.
- Decide whether graphthulhu fallback can be removed after enough daily-driver time on `logseq-mcp`.
- Close the archive hygiene debt if full audit cleanliness matters: reconcile the explicit `FOUN-07` live checkpoint trail and finish Nyquist cleanup for Phases 1 and 3.

## Context

- Codebase state at v1.0: 59 files changed across the milestone and roughly 2,658 lines across `src/` and `tests/`
- Tech stack in use: Python 3.12+, FastMCP, httpx, Pydantic v2, pytest, uv
- User feedback learned during rollout: real shared-graph validation matters because namespaced production pages exposed a payload shape the isolated graph did not
- Operational note: keep both `logseq-mcp` and graphthulhu in the shared MCP config until a deliberate cleanup phase removes the fallback

---
*Last updated: 2026-03-12 after v1.0 milestone completion*
