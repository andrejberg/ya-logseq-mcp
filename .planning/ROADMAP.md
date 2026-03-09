# Roadmap: Logseq MCP Server

## Overview

This roadmap delivers a Python MCP server that replaces graphthulhu for daily-driver Logseq operations. The build is bottom-up: foundation (types, client, server skeleton) first, then read tools with the critical deduplication fix, then write tools, then integration testing and the actual swap. Four phases, 22 requirements, one goal: every read returns correct blocks and every write produces valid Logseq content.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation** - Async client, Pydantic types, MCP server skeleton, and health tool (completed 2026-03-09)
- [ ] **Phase 2: Core Reads** - Deduplicated page reads, block retrieval, page listing, and backlinks
- [ ] **Phase 3: Write Tools** - Page and block CRUD with correct hierarchy
- [ ] **Phase 4: Integration and Swap** - End-to-end verification, parity testing, graphthulhu replacement

## Phase Details

### Phase 1: Foundation
**Goal**: A running MCP server that connects to Logseq, handles auth, serializes requests, and responds to health checks
**Depends on**: Nothing (first phase)
**Requirements**: FOUN-01, FOUN-02, FOUN-03, FOUN-04, FOUN-05, FOUN-06, FOUN-07, FOUN-08
**Success Criteria** (what must be TRUE):
  1. Running `python -m logseq_mcp` starts a server that accepts MCP tool calls over stdio
  2. The `health` tool returns the graph name and page count from a running Logseq instance
  3. All server output goes to stderr; stdout carries only MCP protocol messages
  4. Requests to a stopped Logseq instance fail gracefully with a clear error (no crash, no hang)
  5. Pydantic models parse both `{"id": N}` and bare `N` response formats without error
**Plans**: 3 plans

Plans:
- [ ] 01-01-PLAN.md — Pydantic types + test scaffold (Wave 1)
- [ ] 01-02-PLAN.md — LogseqClient with retry, semaphore, auth (Wave 2)
- [ ] 01-03-PLAN.md — FastMCP server, health tool, lifespan (Wave 3)

### Phase 2: Core Reads
**Goal**: Users can read pages, blocks, page lists, and backlinks with correct deduplicated block trees
**Depends on**: Phase 1
**Requirements**: READ-01, READ-02, READ-03, READ-04, READ-05, READ-06
**Success Criteria** (what must be TRUE):
  1. `get_page` returns a block tree with zero duplicate UUIDs (the primary fix over graphthulhu)
  2. `get_page` preserves correct parent/child nesting -- no blocks promoted or demoted to the wrong level
  3. `get_block` returns a single block by UUID, including its children when requested
  4. `list_pages` returns filtered page lists (by namespace at minimum)
  5. `get_references` returns backlinks for a given page name
**Plans**: 3 plans

Plans:
- [x] 02-01-PLAN.md — test_core.py: failing test stubs for READ-01 through READ-06 (Wave 1)
- [x] 02-02-PLAN.md — get_page with deduplication helpers (Wave 2)
- [ ] 02-03-PLAN.md — get_block, list_pages, get_references (Wave 3)

### Phase 3: Write Tools
**Goal**: Users can create pages, append/update/delete blocks with correct Logseq hierarchy
**Depends on**: Phase 2
**Requirements**: WRIT-01, WRIT-02, WRIT-03, WRIT-04, WRIT-05
**Success Criteria** (what must be TRUE):
  1. `page_create` creates a page with properties that appear correctly in Logseq's UI
  2. `block_append` with nested objects produces correct parent/child block hierarchy in Logseq
  3. `block_update` changes block content and the change is visible via `get_page`
  4. `block_delete` removes a block and it no longer appears in `get_page` results
**Plans**: TBD

Plans:
- [ ] 03-01: TBD
- [ ] 03-02: TBD

### Phase 4: Integration and Swap
**Goal**: The server is production-ready and replaces graphthulhu in the MCP config
**Depends on**: Phase 3
**Requirements**: INTG-01, INTG-02, INTG-03
**Success Criteria** (what must be TRUE):
  1. Server runs as MCP stdio transport and Claude Code can invoke all registered tools
  2. Integration tests pass against an isolated test graph (not the real workspace graph)
  3. `get_page` on a known page returns fewer blocks than graphthulhu (deduplication verified)
  4. The server entry in `~/.claude/.mcp.json` replaces graphthulhu and daily workflow is unbroken
**Plans**: TBD

Plans:
- [ ] 04-01: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 3/3 | Complete   | 2026-03-09 |
| 2. Core Reads | 2/3 | In Progress|  |
| 3. Write Tools | 0/? | Not started | - |
| 4. Integration and Swap | 0/? | Not started | - |
