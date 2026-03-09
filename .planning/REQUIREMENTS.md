# Requirements: Logseq MCP Server

**Defined:** 2026-03-09
**Core Value:** Every read returns correctly structured blocks and every write produces valid Logseq content

## v1 Requirements

Requirements for initial release (graphthulhu swap threshold). 9 tools total.

### Foundation

- [ ] **FOUN-01**: Async HTTP client connects to Logseq API with Bearer token auth
- [ ] **FOUN-02**: Client retries on 5xx errors with exponential backoff (100ms initial, 3 retries)
- [ ] **FOUN-03**: Client serializes requests with asyncio.Semaphore(1) to avoid Logseq UI freezes
- [ ] **FOUN-04**: Pydantic models handle polymorphic API responses (both `{"id": N}` and bare `N` formats)
- [ ] **FOUN-05**: MCP server registers tools via FastMCP `@mcp.tool()` decorators
- [ ] **FOUN-06**: All logging goes to stderr only (stdout breaks MCP protocol)
- [ ] **FOUN-07**: `health` tool pings Logseq and returns graph name + page count
- [ ] **FOUN-08**: Server manages httpx.AsyncClient lifecycle via FastMCP lifespan

### Core Reads

- [ ] **READ-01**: `get_page` returns page metadata and block tree deduplicated by UUID
- [ ] **READ-02**: `get_page` preserves correct parent/child nesting (no blocks promoted to wrong level)
- [ ] **READ-03**: `get_page` uses page name (not UUID) for `getPageBlocksTree` calls
- [ ] **READ-04**: `get_block` returns a single block by UUID with optional children
- [ ] **READ-05**: `list_pages` returns pages with optional namespace filter
- [ ] **READ-06**: `get_references` returns backlinks to a page via `getPageLinkedReferences`

### Write Tools

- [ ] **WRIT-01**: `page_create` creates a page with properties and optional initial blocks
- [ ] **WRIT-02**: `block_append` appends blocks to a page, accepting both flat strings and nested `{content, properties, children}` objects
- [ ] **WRIT-03**: `block_append` produces correct Logseq block hierarchy (children nested under parents)
- [ ] **WRIT-04**: `block_update` updates block content by UUID
- [ ] **WRIT-05**: `block_delete` deletes a block by UUID

### Integration

- [ ] **INTG-01**: Server runs as MCP stdio transport via `python -m logseq_mcp`
- [ ] **INTG-02**: Integration tests run against a local test Logseq graph (isolated from real graph)
- [ ] **INTG-03**: Parity verified on `get_page` output vs graphthulhu (same page, fewer/correct blocks)

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### DataScript Query Tools

- **QURY-01**: `query` passes raw DataScript queries to Logseq
- **QURY-02**: `find_by_tag` finds blocks/pages by tag via DataScript with input sanitization
- **QURY-03**: `query_properties` finds blocks/pages by property key/value with input sanitization

### Additional Write Tools

- **WRIT-06**: `delete_page` deletes a page entirely
- **WRIT-07**: `rename_page` renames a page (Logseq updates links automatically)
- **WRIT-08**: `move_block` moves a block to a new location (before, after, or as child)

### Journal Tools

- **JOUR-01**: `journal_today` gets or creates today's journal page
- **JOUR-02**: `journal_append` appends blocks to a journal page by date string
- **JOUR-03**: `journal_range` fetches journal entries for a date range via DataScript

### Kanban Tools

- **KANB-01**: `kanban_get` returns board page with tasks per column
- **KANB-02**: `kanban_move` moves task block to a column
- **KANB-03**: `kanban_add_task` creates task with workspace property schema
- **KANB-04**: `kanban_list` lists tasks by column/project/status

### Template Tools

- **TMPL-01**: `template_list` lists all templates in the graph
- **TMPL-02**: `template_get` gets a template's content by name
- **TMPL-03**: `template_create` creates a template from an existing block
- **TMPL-04**: `template_delete` deletes a template by name
- **TMPL-05**: `template_apply` inserts template at a page or block

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Brute-force search (scan all pages) | Slow, blows context window; use DataScript queries instead |
| Content parsing / link extraction | Agent can read the markdown; lean output by design |
| In-memory graph analysis | Logseq already has the graph; use DataScript queries |
| AI-powered analysis tools | MCP provides data, not interpretation; let LLM analyze |
| Obsidian backend | Logseq-only; removed entirely |
| Flashcard/whiteboard/decision tools | Never used in this workspace |
| Graph caching | Local API is fast; caching adds stale-data complexity |
| Multiple transport modes | stdio only; single-user local server |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| FOUN-01 | — | Pending |
| FOUN-02 | — | Pending |
| FOUN-03 | — | Pending |
| FOUN-04 | — | Pending |
| FOUN-05 | — | Pending |
| FOUN-06 | — | Pending |
| FOUN-07 | — | Pending |
| FOUN-08 | — | Pending |
| READ-01 | — | Pending |
| READ-02 | — | Pending |
| READ-03 | — | Pending |
| READ-04 | — | Pending |
| READ-05 | — | Pending |
| READ-06 | — | Pending |
| WRIT-01 | — | Pending |
| WRIT-02 | — | Pending |
| WRIT-03 | — | Pending |
| WRIT-04 | — | Pending |
| WRIT-05 | — | Pending |
| INTG-01 | — | Pending |
| INTG-02 | — | Pending |
| INTG-03 | — | Pending |

**Coverage:**
- v1 requirements: 22 total
- Mapped to phases: 0
- Unmapped: 22 ⚠️

---
*Requirements defined: 2026-03-09*
*Last updated: 2026-03-09 after initial definition*
