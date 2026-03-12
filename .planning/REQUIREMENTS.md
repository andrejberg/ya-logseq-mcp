# Requirements: Logseq MCP Server

**Defined:** 2026-03-12
**Milestone:** v1.1
**Core Value:** Every read returns correctly structured blocks and every write produces valid Logseq content — no duplicates, no ghost blocks, no broken hierarchy.

## v1.1 Requirements

### Journals

- [ ] **JOUR-01**: User can fetch today's journal page and the server creates it if it does not already exist.
- [ ] **JOUR-02**: User can append blocks to a journal page by `YYYY-MM-DD` date using the same nested block contract as `block_append`.
- [ ] **JOUR-03**: User can fetch journal entries for an inclusive date range and invalid or reversed date ranges fail explicitly.

### Lifecycle Writes

- [ ] **WRIT-06**: User can delete a page by name and the server verifies the page no longer resolves afterward.
- [ ] **WRIT-07**: User can rename a page by old and new name and the server verifies the new page resolves while the old name no longer does.
- [ ] **WRIT-08**: User can move a block subtree by UUID relative to another block using `before`, `after`, or `child` positioning and the server verifies the subtree moved correctly.

## Future Requirements

### DataScript Query Tools

- **QURY-01**: `query` passes raw DataScript queries to Logseq.
- **QURY-02**: `find_by_tag` finds blocks/pages by tag via DataScript with input sanitization.
- **QURY-03**: `query_properties` finds blocks/pages by property key/value with input sanitization.

### Template Tools

- **TMPL-01**: `template_list` lists all templates in the graph.
- **TMPL-02**: `template_get` gets a template's content by name.
- **TMPL-03**: `template_create` creates a template from an existing block.
- **TMPL-04**: `template_delete` deletes a template by name.
- **TMPL-05**: `template_apply` inserts a template at a page or block.

### Other Deferred Work

- **KANB-01**: `kanban_get` returns board page with tasks per column.
- **KANB-02**: `kanban_move` moves a task block to a column.
- **KANB-03**: `kanban_add_task` creates a task with workspace property schema.
- **KANB-04**: `kanban_list` lists tasks by column/project/status.

## Out of Scope

| Feature | Reason |
|---------|--------|
| General DataScript query surface in v1.1 | Keep this milestone focused on journals and lifecycle writes |
| Template tools in v1.1 | Explicitly deferred to a later milestone after journaling and lifecycle parity |
| Brute-force page scanning for journals | Too slow and unnecessary if journal metadata or direct lookup is available |
| Local cache or graph state | Logseq remains the single source of truth |
| Output enrichment/parsing | Lean output remains a core project constraint |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| JOUR-01 | Phase 6 | Pending |
| JOUR-02 | Phase 6 | Pending |
| JOUR-03 | Phase 7 | Pending |
| WRIT-06 | Phase 5 | Pending |
| WRIT-07 | Phase 5 | Pending |
| WRIT-08 | Phase 6 | Pending |

**Coverage:**
- v1.1 requirements: 6 total
- Mapped to phases: 6
- Unmapped: 0

---
*Requirements defined: 2026-03-12*
*Last updated: 2026-03-12 after starting v1.1 milestone planning*
