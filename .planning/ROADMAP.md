# Roadmap: Logseq MCP Server

## Milestones

- ✅ **v1.0 Logseq MCP Server MVP** - Phases 1-4 shipped on 2026-03-12
- 🚧 **v1.1 Journals and Lifecycle Tools** - Phases 5-7 planned
- 📋 **v1.2 Queries and Templates** - Future milestone placeholder

## Phases

<details>
<summary>✅ v1.0 Logseq MCP Server MVP (Phases 1-4) - SHIPPED 2026-03-12</summary>

See `.planning/milestones/v1.0-ROADMAP.md` for the archived milestone roadmap.

</details>

### 🚧 v1.1 Journals and Lifecycle Tools (In Progress)

**Milestone Goal:** Add journal workflows and the remaining page/block lifecycle writes so daily-note and structural maintenance flows no longer require client-side orchestration.

#### Phase 5: Lifecycle Write Semantics
**Goal**: Add verified page lifecycle mutations and settle the shared mutation contract for the remaining write surface.
**Depends on**: Phase 4
**Requirements**: WRIT-06, WRIT-07
**Success Criteria** (what must be TRUE):
1. User can delete a page by name and follow-up reads confirm the page is gone.
2. User can rename a page and the new name resolves while the old name no longer does.
3. Lifecycle write tests cover missing pages, name collisions, and namespaced page behavior.
**Plans**: 2 plans

Plans:
- [x] 05-01: lifecycle write test scaffold and shared verification helpers
- [x] 05-02: `delete_page` and `rename_page`

#### Phase 6: Block Moves and Journal Writes
**Goal**: Deliver move semantics plus ISO journal creation and append flows on top of the existing write architecture.
**Depends on**: Phase 5
**Requirements**: WRIT-08, JOUR-01, JOUR-02
**Success Criteria** (what must be TRUE):
1. User can move a block subtree before, after, or as a child of another block and the moved subtree keeps its hierarchy.
2. User can fetch today's journal page and it is created automatically when absent on graphs using Logseq `yyyy-MM-dd` journal page titles.
3. User can append nested blocks to a journal page by `YYYY-MM-DD` date using the same structural guarantees as `block_append` on graphs using Logseq `yyyy-MM-dd` journal page titles.
**Plans**: 5 plans

Plans:
- [x] 06-01: `move_block` with subtree verification
- [x] 06-02: journal helpers and `journal_today`
- [x] 06-03: `journal_append`
- [x] 06-04: document ISO journal scope and reconcile Phase 6 records
- [x] 06-05: cross-page `move_block` verification and regression coverage

#### Phase 7: Journal Range and Milestone Validation
**Goal**: Finish journal history reads and prove the new tool surface over the real MCP entrypoint and isolated live graph.
**Depends on**: Phase 6
**Requirements**: JOUR-03
**Success Criteria** (what must be TRUE):
1. User can fetch journal entries for an inclusive date range and invalid or reversed ranges fail explicitly.
2. Journal range resolution prefers stable journal metadata or another bounded lookup strategy over brute-force page scanning.
3. The v1.1 tool surface is exposed on the stdio server and validated on the isolated graph for destructive and journal flows.
**Plans**: 3 plans

Plans:
- [ ] 07-01: `journal_range` and date-range validation
- [ ] 07-02: MCP stdio registration and end-to-end tool coverage
- [ ] 07-03: isolated live graph validation and milestone sign-off

### 📋 v1.2 Queries and Templates (Planned)

**Milestone Goal:** Revisit general DataScript query tools and template tools after journal and lifecycle parity ships.

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Foundation | v1.0 | 3/3 | Complete | 2026-03-12 |
| 2. Core Reads | v1.0 | 3/3 | Complete | 2026-03-12 |
| 3. Write Tools | v1.0 | 3/3 | Complete | 2026-03-12 |
| 4. Integration and Swap | v1.0 | 3/3 | Complete | 2026-03-12 |
| 5. Lifecycle Write Semantics | v1.1 | 2/2 | Complete | 2026-03-12 |
| 6. Block Moves and Journal Writes | v1.1 | 5/5 | Complete | 2026-03-12 |
| 7. Journal Range and Milestone Validation | 1/3 | In Progress|  | - |
