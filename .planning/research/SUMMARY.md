# Project Research Summary

**Project:** logseq-mcp
**Domain:** Python MCP server wrapping Logseq HTTP API (replacing graphthulhu)
**Researched:** 2026-03-09
**Confidence:** HIGH

## Executive Summary

This project is a focused rewrite of the graphthulhu MCP server, replacing a Go implementation with a Python one to fix a critical block duplication bug, eliminate verbose output that wastes LLM context windows, and remove ~40% dead code (Obsidian/flashcard/whiteboard). The domain is well-understood: it is a thin async wrapper over Logseq's internal HTTP API (`POST /api` with JSON-RPC-style payloads) exposed as MCP tools via the official Python SDK's FastMCP framework. All dependencies are already locked and current. The architecture is a straightforward four-layer stack (transport, tools, client, types) with no novel patterns required.

The recommended approach is to build bottom-up: types and client first, then progressively add tool modules (core reads, writes, journal). The v1 target is 18 tools that achieve full graphthulhu replacement for daily-driver operations. Kanban and template tools (9 additional) should be deferred to v2 -- they depend on workspace-specific conventions and use underexplored Logseq API methods. The core competitive advantage is correctness (UUID-deduplicated block trees) and efficiency (lean output by default), not feature count.

The key risks are: (1) Logseq's API returns polymorphic response shapes that will break naive Pydantic models -- this must be handled defensively in `types.py` from day one; (2) stdout corruption from any `print()` or misconfigured logging will silently kill the MCP connection; (3) Logseq's API is single-threaded, so concurrent async requests will cause freezes unless serialized with a semaphore. All three are well-understood with clear prevention strategies documented in the pitfalls research.

## Key Findings

### Recommended Stack

The stack is fully locked and requires zero new dependencies. The MCP Python SDK v1.26.0 provides `FastMCP` with decorator-based tool registration and automatic JSON Schema generation from type hints. `httpx` 0.28.1 provides async HTTP with connection pooling. Pydantic 2.12.5 handles data validation with `model_validator(mode='before')` for Logseq's inconsistent response shapes.

**Core technologies:**
- **MCP Python SDK (`mcp` 1.26.0):** FastMCP server framework -- decorator-based tools, stdio transport, lifespan for client lifecycle
- **httpx (0.28.1):** Async HTTP client -- connection pooling, single `AsyncClient` instance via lifespan
- **Pydantic (2.12.5):** Data models -- pre-validators normalize Logseq's polymorphic `{"id": N}` vs bare `N` response formats

**Rejected alternatives:** tenacity (overkill for one retry point), pydantic-settings (two env vars), aiohttp (httpx already locked), respx (integration tests hit real API). No CLI framework needed -- entry point is `mcp.run()`.

### Expected Features

**Must have (table stakes -- 18 tools for v1):**
- `get_page` with UUID deduplication -- the primary reason for the rewrite
- `get_block`, `list_pages`, `get_references` -- standard read operations
- `query`, `find_by_tag`, `query_properties` -- DataScript-based retrieval (replaces brute-force search)
- `page_create`, `block_append`, `block_update`, `block_delete`, `delete_page`, `rename_page`, `move_block` -- write operations
- `journal_today`, `journal_append`, `journal_range` -- daily workflow
- `health` -- connectivity validation

**Should have (differentiators built into v1):**
- Block deduplication by UUID -- no other Logseq MCP addresses this
- Lean output by default -- saves context window vs graphthulhu's always-verbose enrichment
- Unified `block_append` handling both flat strings and nested objects -- single tool instead of two
- Journal date format resilience -- try multiple formats instead of guessing one

**Defer to v2:**
- `kanban_get`, `kanban_move`, `kanban_add_task`, `kanban_list` -- workspace-specific conventions, not daily-driver yet
- `template_list`, `template_get`, `template_create`, `template_delete`, `template_apply` -- underutilized Logseq API, add when template workflow matures

**Anti-features (never build):**
- Brute-force search (scan all pages) -- use DataScript instead
- Content parsing / link extraction -- agent can read the markdown
- In-memory graph analysis or AI-powered tools -- let the calling LLM do analysis
- Vault/graph caching -- Logseq API is local and fast, caching adds stale-data bugs

### Architecture Approach

Four-layer architecture: transport (FastMCP/stdio), tools (domain logic per module), client (async HTTP facade with retry and semaphore), types (Pydantic models). The FastMCP lifespan manages `httpx.AsyncClient` lifecycle. Tool modules self-register via `@mcp.tool()` decorators and are imported by `__main__.py` to avoid circular imports. Domain logic (deduplication, DataScript query construction, response formatting) lives in the tool layer; the client layer returns raw typed responses faithfully.

**Major components:**
1. **`server.py`** -- FastMCP instance, lifespan (client lifecycle), `get_client()` accessor
2. **`client.py`** -- `LogseqClient` wrapping `httpx.AsyncClient`, retry logic, semaphore for request serialization, auth headers
3. **`types.py`** -- `PageEntity`, `BlockEntity`, `PageRef`, `BlockRef` with pre-validators for polymorphic API responses
4. **`tools/core.py`** -- Read tools with block deduplication and DataScript query construction
5. **`tools/write.py`** -- Write tools with input validation for flat vs nested blocks
6. **`tools/journal.py`** -- Journal tools with date format handling and DataScript-based range queries

### Critical Pitfalls

1. **Block duplication in tree traversal** -- Deduplicate by UUID with a `seen` set during any block tree walk. Test by comparing block count against Logseq UI. This is the reason for the rewrite.
2. **stdout corruption kills MCP connection** -- Configure ALL logging to stderr from day one. Never use bare `print()`. Test with MCP Inspector before integration.
3. **Logseq API response polymorphism** -- Use Pydantic `model_validator(mode='before')` to handle both `{"id": N}` and bare `N` formats. Wrap parsing in try/except with fallback to raw JSON.
4. **Logseq API is single-threaded** -- Add `asyncio.Semaphore(1)` in client to serialize requests. Use DataScript queries instead of loops of individual API calls (especially for `journal_range`).
5. **`getPageBlocksTree` UUID parameter is broken** -- Always pass page names, never UUIDs. Resolve UUID to name first if needed.
6. **Page properties vs block properties** -- `createPage(name, properties, opts)` sets page properties (second arg). `insertBlock` `properties` option sets block-level properties. These are different systems.
7. **DataScript injection** -- Sanitize user inputs in `find_by_tag` and `query_properties`. Investigate `:in` clause for parameterized queries.

## Implications for Roadmap

### Phase 1: Foundation
**Rationale:** Everything depends on the type system, HTTP client, and server skeleton. Pitfalls 2 (stdout), 3 (polymorphism), 4 (single-threaded API), and 6 (UUID param bug) must be addressed here or they cascade into every subsequent phase.
**Delivers:** Working MCP server that connects to Logseq and responds to `health` checks. Correct logging to stderr. Semaphore-serialized client. Defensive Pydantic models.
**Addresses:** `health` tool, project infrastructure
**Avoids:** stdout corruption (Pitfall 2), response format crashes (Pitfall 3), concurrent request freezes (Pitfall 5), UUID param bug (Pitfall 6)
**Components:** `types.py`, `client.py`, `server.py`, `__main__.py`, `tools/core.py` (health only)

### Phase 2: Core Reads
**Rationale:** Read tools are needed to verify that writes work correctly. `get_page` with deduplication is the primary value proposition. DataScript tools (`query`, `find_by_tag`, `query_properties`) are needed by later phases (kanban, journal_range).
**Delivers:** 7 read tools -- the full read surface of the MCP server. Block deduplication verified against real Logseq data.
**Addresses:** `get_page`, `get_block`, `list_pages`, `get_references`, `query`, `find_by_tag`, `query_properties`
**Avoids:** Block duplication (Pitfall 1), DataScript injection (Pitfall 7)
**Components:** `tools/core.py` (all read tools), query sanitization utility

### Phase 3: Write Tools
**Rationale:** Writes depend on the client (Phase 1) and benefit from reads for verification (Phase 2). The page vs block property distinction (Pitfall 4) is the main complexity.
**Delivers:** 7 write tools -- full CRUD on pages and blocks.
**Addresses:** `page_create`, `block_append`, `block_update`, `block_delete`, `delete_page`, `rename_page`, `move_block`
**Avoids:** Wrong property level (Pitfall 4, properties research), child order reversal in nested appends

### Phase 4: Journal Tools
**Rationale:** Journal tools depend on page reads (Phase 2) and block writes (Phase 3). `journal_range` must use DataScript `journal-day` queries (not N page lookups) to avoid the single-threaded API bottleneck.
**Delivers:** 3 journal tools -- daily workflow support.
**Addresses:** `journal_today`, `journal_append`, `journal_range`
**Avoids:** Date format guessing failures, N-page-lookup performance trap

### Phase 5: Integration and Swap
**Rationale:** The 18 v1 tools are complete. Run both MCPs side-by-side, verify parity on `get_page`, `journal_today`, and key write operations, then swap `.mcp.json` to the new server.
**Delivers:** Production deployment -- graphthulhu replaced.
**Addresses:** MCP config in `~/.claude/.mcp.json`, parity verification
**Avoids:** Breaking daily workflow by swapping before verification

### Phase 6: Kanban Tools (v2)
**Rationale:** Workspace-specific conventions. Not needed for graphthulhu replacement. Can be added without architectural changes since the tool module pattern is established.
**Delivers:** 4 kanban tools with hardcoded column names.
**Addresses:** `kanban_get`, `kanban_move`, `kanban_add_task`, `kanban_list`

### Phase 7: Template Tools (v2)
**Rationale:** Uses underutilized `App.*` API methods. Low urgency, add when template workflow matures.
**Delivers:** 5 template CRUD + apply tools.
**Addresses:** `template_list`, `template_get`, `template_create`, `template_delete`, `template_apply`

### Phase Ordering Rationale

- **Bottom-up by dependency:** Types before client before server before tools. Each layer is testable in isolation before the next is built.
- **Reads before writes:** You need reads to verify writes work correctly. `get_page` deduplication (the rewrite's raison d'etre) must be proven correct early.
- **Journal after writes:** `journal_append` reuses `block_append` logic; `journal_today` may create pages. These need working write infrastructure.
- **Integration as a gate:** Phase 5 is a validation gate before adding workspace-specific tools. If parity is not achieved, fixing core tools takes priority over new features.
- **v2 tools are additive:** Kanban and templates use the same client/server infrastructure. They are independent modules that can be added in any order.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 3 (Write Tools):** The page vs block property distinction is subtle and the API behavior is underdocumented. Integration tests against live Logseq are essential. Research `insertBatchBlock` reliability (GitHub issue #11426 reports block loss).
- **Phase 4 (Journal):** Date format handling across locales needs investigation with the actual Logseq instance. DataScript `journal-day` integer format must be verified.
- **Phase 6 (Kanban):** Column name matching and task property schema are workspace-specific. Needs validation against actual graph data.

Phases with standard patterns (skip research-phase):
- **Phase 1 (Foundation):** All patterns verified in MCP SDK source code, httpx docs, and Pydantic docs. HIGH confidence.
- **Phase 2 (Core Reads):** DataScript queries proven in graphthulhu. Deduplication algorithm is straightforward. HIGH confidence.
- **Phase 5 (Integration):** Standard MCP config swap. No research needed.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All deps already locked and current. MCP SDK, httpx, Pydantic are mature, well-documented. Zero new dependencies needed. |
| Features | HIGH | Clear reference implementation (graphthulhu). Competitive landscape well-mapped. MVP scope (18 tools) is well-defined. |
| Architecture | HIGH | Four-layer pattern verified in MCP SDK source. FastMCP lifespan, decorator registration, and error handling all confirmed. |
| Pitfalls | HIGH | Primary pitfalls derived from confirmed graphthulhu bugs and Logseq GitHub issues. Prevention strategies are concrete. |

**Overall confidence:** HIGH

### Gaps to Address

- **`insertBatchBlock` reliability:** Logseq issue #11426 reports block loss with batch inserts. May need to fall back to sequential inserts for nested writes in Phase 3. Test empirically.
- **Logseq `App.*` template API stability:** These methods are less commonly used than `Editor.*` methods. Verify they exist and work correctly in the current Logseq version before Phase 7.
- **DataScript `:in` clause for parameterized queries:** Research whether `datascriptQuery` accepts additional args for parameterized queries to avoid string interpolation in `find_by_tag` and `query_properties`.
- **Journal date format for this Logseq instance:** The actual format depends on Logseq's `:journal/page-title-format` config. Verify the format used in this workspace before Phase 4.
- **Short-TTL caching for `getAllPages`:** Identified as technical debt to address post-MVP. The same page list may be fetched multiple times in one LLM turn. A 5-10 second TTL cache in the client would help.

## Sources

### Primary (HIGH confidence)
- MCP Python SDK v1.26.0 -- FastMCP API, lifespan pattern, tool registration, error handling
- httpx 0.28.1 documentation -- AsyncClient lifecycle, connection pooling
- Pydantic 2.12.5 documentation -- model_validator, field_validator patterns
- graphthulhu source code -- API call patterns, DataScript queries, type models, confirmed bugs

### Secondary (HIGH confidence)
- [ergut/mcp-logseq](https://github.com/ergut/mcp-logseq) -- 15-tool TypeScript reference
- [joelhooks/logseq-mcp-tools](https://github.com/joelhooks/logseq-mcp-tools) -- feature comparison (anti-patterns identified)
- [saichaitanyam/LogseqMCP](https://github.com/saichaitanyam/LogseqMCP) -- FastMCP Python reference
- [MCP Best Practices - philschmid](https://www.philschmid.de/mcp-best-practices) -- tool design patterns
- Logseq GitHub issues #4920, #11435, #11372, #11426 -- confirmed API bugs

### Tertiary (MEDIUM confidence)
- [dailydaniel/logseq-mcp](https://github.com/dailydaniel/logseq-mcp) -- minimal Python reference
- [Less is More - Klavis AI](https://www.klavis.ai/blog/less-is-more-mcp-design-patterns-for-ai-agents) -- MCP design patterns

---
*Research completed: 2026-03-09*
*Ready for roadmap: yes*
