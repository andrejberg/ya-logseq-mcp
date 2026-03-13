# ya-logseq-mcp

## What This Is

A Python MCP server for Logseq that replaces graphthulhu for daily-driver reads and writes in this workspace, with strict structure correctness, lean payloads, and verified transport coverage.

## Core Value

Every read returns correctly structured blocks and every write produces valid Logseq content - no duplicates, no ghost blocks, no broken hierarchy.

## Current Milestone: v1.2 Packaging and GitHub Release

**Goal:** Ship the current functional MCP as a renamed, documented, publish-ready project without adding new MCP features.

**Target features:**
- Move repository from `~/Workspace/projects/logseq-mcp` to `~/Workspace/tools/ya-logseq-mcp`
- Update local/runtime configuration for the new path and project name
- Refresh docs for renamed branding and release readiness
- Improve installation/setup instructions for usability and first-run success
- Publish repository to GitHub under the new name

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

- [ ] Project is renamed to `ya-logseq-mcp` across package, repo, and documentation
- [ ] Repository is relocated to `~/Workspace/tools/ya-logseq-mcp` with working dev/test commands
- [ ] Runtime/config references are updated and validated for the new location/name
- [ ] Installation instructions are user-friendly and verified end-to-end
- [ ] Repository is published on GitHub with clear setup/usage docs

### Out of Scope

- Kanban tools (kanban_get, kanban_move, kanban_add_task, kanban_list) - not daily-driver; defer to v2+
- Obsidian backend - removed entirely, Logseq-only
- Flashcard/whiteboard/decision tools - never used
- Content parsing (extracting links/tags from block content) - lean output by design
- In-memory graph analysis - not needed; Logseq is source of truth
- Brute-force page scanning for journals - rejected in favor of bounded date lookup
- Query and template tools (`query`, `find_by_tag`, `query_properties`, `template_*`) - deferred to a future milestone after release hardening

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
| Keep query/template tools for v1.2 | Preserve v1.1 scope and shipping velocity | ⚠️ Revisit |
| Prioritize shipping current toolset before new capabilities | Reduce integration risk and improve adoption path | — Pending |

## Current State

- Shipped milestones: `v1.0` (2026-03-12), `v1.1` (2026-03-13 archive/tag cycle)
- Delivered surface now includes all v1.0 + v1.1 tools (`journal_today`, `journal_append`, `journal_range`, `delete_page`, `rename_page`, `move_block`)
- Validation status: unit + server registry + MCP stdio + isolated live graph evidence complete for v1.1
- Audit status: requirement/integration/flow coverage complete; Nyquist debt remains for phases 05 and 06

## Next Milestone Goals

- Rename and package the project as `ya-logseq-mcp` for external use.
- Move the repository into `~/Workspace/tools` and fix all path/config assumptions.
- Raise documentation quality, especially installation clarity and onboarding flow.
- Publish to GitHub once naming, configuration, and docs are coherent.

---
*Last updated: 2026-03-13 after starting v1.2 packaging and release milestone*
