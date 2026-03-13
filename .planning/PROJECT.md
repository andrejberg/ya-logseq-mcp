# Logseq MCP Server

## What This Is

A Python MCP server for Logseq that replaces graphthulhu for daily-driver reads and writes in this workspace, with strict structure correctness, lean payloads, and verified transport coverage.

## Core Value

Every read returns correctly structured blocks and every write produces valid Logseq content - no duplicates, no ghost blocks, no broken hierarchy.

## Current Milestone: v1.2 Queries and Templates

**Goal:** Add scoped query and template tools after v1.1 shipped journaling and lifecycle parity.

**Target features:**
- `query`
- `find_by_tag`
- `query_properties`
- `template_list`
- `template_get`
- `template_create`
- `template_delete`
- `template_apply`

## Requirements

### Validated

- ✓ Async HTTP client talks to Logseq API with retry/auth and single-flight request serialization - v1.0
- ✓ `health` verifies live Logseq connectivity over the production MCP server entrypoint - v1.0
- ✓ `get_page` returns deduplicated block trees with correct parent/child nesting - v1.0
- ✓ `get_block`, `list_pages`, and `get_references` cover the core daily-driver read surface - v1.0
- ✓ `page_create`, `block_append`, `block_update`, and `block_delete` produce valid Logseq content and verify mutations through follow-up reads - v1.0
- ✓ Integration coverage runs against an isolated graph and proves parity against graphthulhu on the fixed fixture page - v1.0
- ✓ `journal_today` gets or creates today's journal page on ISO-title Logseq graphs - v1.1
- ✓ `journal_append` appends nested blocks to a journal page by `YYYY-MM-DD` date - v1.1
- ✓ `journal_range` returns inclusive date windows with explicit invalid/reversed-range errors - v1.1
- ✓ `delete_page` deletes a page and verifies non-resolution after mutation - v1.1
- ✓ `rename_page` renames a page and verifies old-name failure plus new-name resolution - v1.1
- ✓ `move_block` supports before/after/child including cross-page subtree verification - v1.1

### Active

- [ ] `query` passes raw DataScript queries to Logseq with explicit error handling
- [ ] `find_by_tag` finds blocks/pages by tag with input sanitization
- [ ] `query_properties` finds blocks/pages by property key/value with input sanitization
- [ ] `template_list` lists all templates in the graph
- [ ] `template_get` gets a template's content by name
- [ ] `template_create` creates a template from an existing block
- [ ] `template_delete` deletes a template by name
- [ ] `template_apply` inserts a template at a page or block

### Out of Scope

- Kanban tools (kanban_get, kanban_move, kanban_add_task, kanban_list) - not daily-driver; defer to v2+
- Obsidian backend - removed entirely, Logseq-only
- Flashcard/whiteboard/decision tools - never used
- Content parsing (extracting links/tags from block content) - lean output by design
- In-memory graph analysis - not needed; Logseq is source of truth
- Brute-force page scanning for journals - rejected in favor of bounded date lookup

## Context

- Codebase state after v1.1: journal and lifecycle write surface is fully shipped, tested at unit/server/stdio/live layers, and recorded in milestone archives.
- Tech stack in use: Python 3.12+, FastMCP, httpx, Pydantic v2, pytest, uv.
- User feedback carried forward: real shared-graph behavior must remain part of acceptance because namespaced and lifecycle behavior differs from isolated fixtures.
- Quality note: v1.1 audit status is `tech_debt` due to partial Nyquist compliance in phases 05 and 06 despite full requirement and integration coverage.

## Constraints

- **Tech stack:** Python >=3.12, uv, httpx (async), Pydantic, MCP SDK.
- **API dependency:** Logseq desktop must run with HTTP API enabled on port 12315.
- **No local state:** Server is stateless; Logseq is the source of truth.
- **Block structure:** Writes must preserve valid Logseq hierarchy.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Python over Go | Maintainability and debuggability; API is HTTP-bound | ✓ Good |
| Lean output by default | Avoid graphthulhu verbosity and reduce client parsing burden | ✓ Good |
| Deduplicate by UUID | Fix duplicated block trees | ✓ Good |
| Local isolated test graph | Prevent destructive integration tests from touching real notes | ✓ Good |
| Bounded date lookup for journals | Deterministic JOUR-03 behavior without brute-force scans | ✓ Good |
| Keep query/template tools for v1.2 | Preserve v1.1 scope and shipping velocity | ✓ Good |

## Current State

- Shipped milestones: `v1.0` (2026-03-12), `v1.1` (2026-03-13 archive/tag cycle)
- Delivered surface now includes all v1.0 + v1.1 tools (`journal_today`, `journal_append`, `journal_range`, `delete_page`, `rename_page`, `move_block`)
- Validation status: unit + server registry + MCP stdio + isolated live graph evidence complete for v1.1
- Audit status: requirement/integration/flow coverage complete; Nyquist debt remains for phases 05 and 06

## Next Milestone Goals

- Define v1.2 requirements and roadmap with clear non-goals before execution.
- Implement query tools first (`query`, `find_by_tag`, `query_properties`) with tight input validation.
- Implement template tools second with parity between direct and stdio flows.
- Keep graphthulhu fallback only until v1.2 verification confirms no regressions in existing shipped behavior.

---
*Last updated: 2026-03-13 after completing v1.1 milestone archival*
