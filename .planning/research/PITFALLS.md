# Pitfalls Research

**Domain:** Python MCP server wrapping Logseq HTTP API (replacing graphthulhu)
**Researched:** 2026-03-09
**Confidence:** HIGH (based on confirmed graphthulhu bugs, Logseq API issues, MCP SDK documentation)

## Critical Pitfalls

### Pitfall 1: Block Duplication in Tree Traversal

**What goes wrong:**
`getPageBlocksTree` returns blocks with children already nested inline. If you then recursively walk children and re-attach them (as graphthulhu's `enrichBlockTree` does at lines 443-460), every child appears both in its parent's `children` array AND as a top-level enriched block. This produces 4-8x duplication on pages with nested blocks.

**Why it happens:**
The Logseq API returns a fully-nested tree. Graphthulhu's enrichment function walks recursively and appends child enriched blocks back onto `eb.BlockEntity.Children`, doubling every level of nesting. The developer assumed children needed to be re-collected, not realizing the API already nested them.

**How to avoid:**
Deduplicate by UUID using a `seen: set[str]` during any tree traversal. Before processing any block, check if its UUID is in `seen`. Better yet, trust the tree structure from `getPageBlocksTree` and do not re-walk children that are already present in the tree. The Python implementation should have a single `walk_block_tree()` function that tracks seen UUIDs and skips duplicates.

**Warning signs:**
- Block count in tool output is 4-8x higher than what Logseq UI shows for the same page
- The same UUID appears multiple times in a `get_page` response
- Unit test: compare `len(result_blocks)` against `len(set(b.uuid for b in result_blocks))`

**Phase to address:**
Phase 2 (Core Reads) -- this is the `get_page` implementation. Must be tested with a page that has 3+ levels of nesting.

---

### Pitfall 2: stdout Corruption in STDIO-Based MCP Servers

**What goes wrong:**
MCP uses stdout for JSON-RPC protocol messages. Any `print()` call, logging to stdout, or library that writes to stdout corrupts the protocol stream and crashes the MCP connection silently. The client sees malformed JSON and disconnects.

**Why it happens:**
Python's `print()` defaults to stdout. `logging.basicConfig()` without explicit `stream=sys.stderr` also defaults to stdout. Third-party libraries (httpx debug logging, Pydantic validation warnings) may write to stdout unexpectedly.

**How to avoid:**
1. Configure all logging to stderr explicitly: `logging.basicConfig(stream=sys.stderr)`
2. Never use bare `print()` -- always `print(..., file=sys.stderr)` or use the logger
3. Set httpx logger to stderr
4. Test the server with the MCP Inspector tool before integration with Claude

**Warning signs:**
- MCP client disconnects immediately after tool call
- "Invalid JSON" errors in the MCP client logs
- Server "works" in unit tests but fails when run as an MCP server

**Phase to address:**
Phase 1 (Foundation) -- the server skeleton and logging setup. Must be correct from the start because every subsequent phase depends on it.

---

### Pitfall 3: Logseq API Response Format Polymorphism

**What goes wrong:**
The Logseq API returns the same logical entity in different shapes depending on which method returned it. Pydantic models that work for one method fail silently or crash for another:
- `BlockEntity.children` can be full block objects OR compact `[["uuid", "value"]]` arrays
- `PageRef` and `BlockRef` can be `{"id": N}` objects OR plain integers
- `getPageLinkedReferences` returns `[[PageEntity, [BlockEntity, ...]], ...]` -- nested arrays, not typed objects
- `getBlock` with `includeChildren: true` returns compact child refs, not full children

**Why it happens:**
The Logseq API is an internal plugin API, not a stable public API. Different code paths in Logseq serialize entities differently. There is no formal schema or contract.

**How to avoid:**
Use Pydantic validators that handle both formats (graphthulhu does this with custom `UnmarshalJSON`). Specifically:
- `BlockEntity`: use a validator on `children` that tries full parse first, falls back to empty list for compact format
- `PageRef`/`BlockRef`: use `@field_validator` that accepts both `int` and `dict` forms
- `getPageLinkedReferences`: parse as `list[tuple[dict, list[dict]]]` with manual extraction, not a Pydantic model
- Always wrap API response parsing in try/except with fallback to raw JSON

**Warning signs:**
- `ValidationError` from Pydantic on specific pages but not others
- Tools work on simple pages but crash on pages with block references or embeds
- `get_block` works but `get_page` crashes (or vice versa) on the same block

**Phase to address:**
Phase 1 (Foundation) -- `types.py` must handle polymorphism from day one. Write unit tests with captured real API responses for each format variant.

---

### Pitfall 4: Properties Embedded in Block Content vs. Properties Object

**What goes wrong:**
Logseq stores page properties as `key:: value` lines in the first block's content. When writing properties via the API, developers often set them as a `properties` dict in `appendBlockInPage` options, but this creates block-level properties (invisible in page property queries). Or they append `key:: value` to content but the property line ends up in the wrong block (not the first/pre-block), making Logseq ignore it as a page property.

**Why it happens:**
Logseq has two distinct property systems: page properties (first block with `preBlock: true`) and block properties (any block's `properties` field). The API's `properties` option on `insertBlock`/`appendBlockInPage` sets block-level properties. Page properties must be written as content lines in the first block. This distinction is not documented in the API.

**How to avoid:**
- For `page_create`: use `createPage(name, properties, opts)` where `properties` is the second arg -- this correctly sets page properties
- For updating page properties: find the first block (`preBlock: true`), modify its content string, call `updateBlock`
- For block properties: use the `properties` option on `insertBlock`/`appendBlockInPage`
- Never assume `properties` in API options sets page-level properties
- In `block_append`, only pass `properties` as block-level properties, never as page properties

**Warning signs:**
- Properties appear in the API response `properties` field but not in Logseq's page properties panel
- DataScript queries for `[:block/properties :property-name]` don't find pages that visually show the property
- `query_properties` returns no results for properties you just created

**Phase to address:**
Phase 3 (Write Tools) -- `page_create` and `block_append` must handle this correctly. Phase 2 should verify by reading back properties after a write in integration tests.

---

### Pitfall 5: Logseq API is Single-Threaded and Blocks on Long Operations

**What goes wrong:**
The Logseq HTTP API processes requests on its main Electron thread. Sending concurrent async requests from Python (natural with httpx.AsyncClient) queues them at the Logseq side. Burst traffic (e.g., `journal_range` for 30 days, `list_pages` with per-page block fetches) causes timeouts, UI freezes in Logseq, and intermittent failures that are hard to reproduce.

**Why it happens:**
Developers assume an HTTP API can handle concurrent requests. Python's async makes it trivially easy to fire many requests in parallel. But Logseq's API is not a web server -- it is an Electron app's internal endpoint.

**How to avoid:**
- Use an `asyncio.Semaphore(1)` in the HTTP client to serialize all requests
- Prefer DataScript queries over loops of individual API calls (e.g., `journal_range` should use a single DataScript query with `journal-day` integer range, not N page lookups)
- Use `insertBatchBlock` instead of sequential `insertBlock` calls for nested writes
- Set a generous timeout (30s) but never retry indefinitely

**Warning signs:**
- Tools work individually but fail when called in sequence during an LLM session
- Logseq desktop freezes or becomes unresponsive during MCP operations
- Intermittent timeouts that don't reproduce when tested in isolation

**Phase to address:**
Phase 1 (Foundation) -- `client.py` must have the semaphore from the start. Phase 4 (Journal) must use DataScript for `journal_range`.

---

### Pitfall 6: `getPageBlocksTree` UUID Parameter Does Not Work

**What goes wrong:**
Despite the API documentation suggesting `getPageBlocksTree` accepts either a page name or page UUID, passing a UUID returns `null` or an empty array. Only page names work reliably.

**Why it happens:**
This is a confirmed Logseq bug (GitHub issue #4920, #11435). The method's internal resolution path for UUIDs is broken in most Logseq versions.

**How to avoid:**
Always pass page names (strings) to `getPageBlocksTree`, never UUIDs. If you have a UUID, first resolve it to a page name via `getPage(uuid)`, then call `getPageBlocksTree(page.name)`. Document this in the client as a known API limitation.

**Warning signs:**
- `get_page` returns empty blocks array when called with a UUID
- Works fine when the same page is looked up by name

**Phase to address:**
Phase 1 (Foundation) -- `client.py` should always normalize to page name before calling `getPageBlocksTree`.

---

### Pitfall 7: DataScript Query Injection

**What goes wrong:**
User-supplied values (tag names, property names, property values) are interpolated directly into DataScript query strings with `fmt.Sprintf` / f-strings. A property value containing `"]` or `"` breaks the query syntax. A malicious input could inject arbitrary Clojure expressions.

**Why it happens:**
DataScript queries are strings, and the Logseq API has limited support for parameterized queries. Graphthulhu's `find_by_tag` and `query_properties` both use direct string interpolation (search.go lines 159-169, 223-226).

**How to avoid:**
- Sanitize all user inputs: strip/escape `"`, `]`, `[`, `\` characters before interpolation
- For property names: validate against `^[a-zA-Z][a-zA-Z0-9_-]*$` pattern
- For tag names: lowercase and strip characters outside `[a-z0-9-_/]`
- The `logseq.DB.datascriptQuery` method accepts additional input arguments after the query string -- investigate whether these can be used as parameterized inputs (`:in` clause) to avoid interpolation entirely
- The raw `query` tool is intentionally unfiltered (power-user tool), but `find_by_tag` and `query_properties` must sanitize

**Warning signs:**
- Tools crash with "invalid query" errors on tags/properties containing special characters
- DataScript error messages leak query structure to the LLM

**Phase to address:**
Phase 2 (Core Reads) -- implement sanitization in `find_by_tag` and `query_properties`. Build a small query builder utility with escaping.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Broad `mcp>=1.0.0` dep range | Picks up latest features | Breaking change on `uv sync` crashes server | Never -- pin to `mcp>=1.0.0,<2.0.0` before first real implementation |
| No request caching in client | Simpler code | `getAllPages` called 3x in one LLM turn wastes time | MVP only -- add TTL cache (5s) in Phase 2 |
| String-building DataScript queries | Quick to implement | Injection risk, hard to maintain | Phase 2 only -- extract query builder by end of Phase 2 |
| No integration tests against live Logseq | Faster development | Can't verify correctness without manual testing | Phase 1-2 only -- must have integration test harness by Phase 3 |
| Hardcoded Kanban column names | Matches current workspace | Silent breakage if conventions change | Acceptable for v1 -- make configurable in v2 |

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Logseq `createPage` | Passing `properties` as third arg creates a page but properties are ignored silently | `properties` is the second arg: `createPage(name, properties, opts)` -- `opts` is for `redirect`, `createFirstBlock`, etc. |
| Logseq `getBlock` with children | Expecting full `BlockEntity` children | Returns compact `[["uuid", "value"]]` refs -- must re-fetch each child via `getBlock` if full data needed, or accept compact form |
| Logseq `moveBlock` | Using positional flags (`before: true`) alone | Must also pass the correct target UUID -- `moveBlock(srcUUID, targetUUID, {before: true})` moves src before target, not to the start of target's children |
| Logseq `appendBlockInPage` | Appending to a page that doesn't exist | Silently creates the page -- verify page existence first if creation is not intended |
| Logseq `updateBlock` with properties | Setting properties via `properties` option | Properties in content (`key:: value` lines) must be part of the content string, not the options object |
| MCP SDK tool registration | Returning plain strings from tool handlers | Must return `CallToolResult` with `TextContent` wrapped content and explicit `isError` flag -- plain strings work in tests but fail at protocol level |

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Journal date format guessing (4 API calls per day) | `journal_range` for 30 days makes 120 API calls, takes 30+ seconds | Use DataScript query on `journal-day` integer: single API call for any range | Any range > 7 days |
| `list_pages` with tag filter (O(N) page scans) | 500-page graph takes 60+ seconds for a tag filter | Use DataScript query with `:block/refs` -- single API call | Any graph with > 50 pages |
| No getAllPages caching | Same page list fetched 3x in one session costs 3 seconds | TTL cache (5-10 seconds) in client | When LLM chains multiple read tools |
| Large page block trees as JSON | `get_page` on a 500-block page returns 100KB+ JSON, burning LLM context | Default `maxBlocks` limit (e.g., 100), truncation with indicator | Pages with > 100 blocks |
| Sequential child block inserts | Inserting 10 nested blocks = 10 API calls | Use `insertBatchBlock` for nested structures | Any nested write with > 3 children |

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| DataScript injection via `find_by_tag` / `query_properties` | Malformed queries crash Logseq or leak graph structure | Sanitize inputs, use parameterized queries where possible |
| No token validation at startup | Server starts without auth, all requests fail silently with 403 | Fail fast at startup if `LOGSEQ_API_TOKEN` is empty |
| Destructive tools without metadata | LLM calls `delete_page` or `block_delete` casually | Add `"destructive": true` in tool description metadata so LLMs treat them cautiously |
| Raw `query` tool allows arbitrary DataScript | Could read any data in the graph including private pages | Document the risk; this is intentional for power users, but the LLM should be aware |

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Verbose JSON responses with all block metadata | LLM wastes context tokens parsing unused fields (pathRefs, left, parent IDs) | Lean responses by default: only uuid, content, children, properties. Add `verbose` flag for full data |
| Error messages showing internal Python tracebacks | LLM gets confused by stack traces and tries to "fix" the code | Return structured error messages: `{"error": "Page not found", "page": "foo", "suggestion": "Check page name spelling"}` |
| Returning `preBlock` (property block) as a regular block | LLM sees raw property lines like `type:: Task` as content and tries to edit them as text | Filter `preBlock` blocks from `get_page` output, or mark them distinctly so the LLM knows they are properties |
| No truncation indicator on large pages | LLM doesn't know it received partial data and makes incorrect assumptions | Always include `truncated: true` and `totalBlocks: N` when output is limited |

## "Looks Done But Isn't" Checklist

- [ ] **`get_page`:** Often missing UUID deduplication -- verify by comparing block count against Logseq UI block count on a page with 3+ nesting levels
- [ ] **`get_page`:** Often missing `preBlock` handling -- verify that the first block (page properties) is either excluded or clearly marked
- [ ] **`block_append` with nested children:** Often reverses child order -- verify that children appear in the same order they were passed in
- [ ] **`journal_today`:** Often fails on first call of the day because journal page doesn't exist yet -- verify it creates the page if missing
- [ ] **`journal_range`:** Often silently returns empty for valid dates because date format doesn't match -- verify with DataScript `journal-day` query as cross-check
- [ ] **Error handling:** Often returns success with empty data instead of error -- verify that `get_page("nonexistent")` returns `isError: true`, not `{"blocks": []}`
- [ ] **MCP tool registration:** Often missing input schema validation -- verify that calling a tool with missing required args returns a clear error, not a Python TypeError
- [ ] **Logging setup:** Often logs to stdout, breaking MCP protocol -- verify by running server with MCP Inspector and checking for protocol errors

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Block duplication in output | LOW | Add UUID dedup in `get_page` -- no data loss, just fix the traversal |
| stdout corruption | LOW | Fix logging config to stderr, restart server |
| Wrong property level (block vs page) | MEDIUM | Delete incorrectly-created blocks, recreate with correct approach. Graph is git-tracked. |
| DataScript injection causes bad data | LOW | DataScript queries are read-only, no data mutation possible. Fix the query builder. |
| Concurrent requests freeze Logseq | LOW | Add semaphore, restart Logseq. No data loss. |
| API response format mismatch crashes Pydantic | MEDIUM | Add defensive parsing with try/except. Capture the failing response for test fixtures. |

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Block duplication | Phase 2 (Core Reads) | Unit test: `len(blocks) == len(set(b.uuid for b in blocks))` on 3-level nested page |
| stdout corruption | Phase 1 (Foundation) | Run with MCP Inspector, verify no protocol errors |
| Response format polymorphism | Phase 1 (Foundation) | Unit tests with captured real API responses for each variant |
| Properties page vs block | Phase 3 (Write Tools) | Integration test: create page with properties, read back, verify properties appear in `getPage` response |
| Single-threaded API | Phase 1 (Foundation) | Semaphore in client; load test with 10 rapid sequential calls |
| UUID param broken in getPageBlocksTree | Phase 1 (Foundation) | Always resolve to page name in client; document in code |
| DataScript injection | Phase 2 (Core Reads) | Unit test with special characters in tag/property inputs |
| Journal date format | Phase 4 (Journal) | Use DataScript `journal-day` query; verify against 30-day range |

## Sources

- graphthulhu source code: `enrichBlockTree` (tools/navigate.go:443-460), `QueryProperties` (tools/search.go:157-169), `FindByTag` (tools/search.go:223-226), `journalPageNames` (tools/journal.go:90-99), `BulkUpdateProperties` (tools/write.go:261-314), `BlockEntity.UnmarshalJSON` (types/logseq.go:48-73)
- [Logseq getPageBlocksTree UUID bug - GitHub issue #4920](https://github.com/logseq/logseq/issues/4920)
- [Logseq REST API page reference problems - GitHub issue #11435](https://github.com/logseq/logseq/issues/11435)
- [Logseq HTTP API method name mismatch - GitHub issue #11372](https://github.com/logseq/logseq/issues/11372)
- [Logseq insertBatchBlock block loss - GitHub issue #11426](https://github.com/logseq/logseq/issues/11426)
- [MCP SDK Python - error handling with isError and TextContent](https://apxml.com/courses/getting-started-model-context-protocol/chapter-3-implementing-tools-and-logic/error-handling-reporting)
- [MCP stdio transport - stdout vs stderr](https://medium.com/@laurentkubaski/understanding-mcp-stdio-transport-protocol-ae3d5daf64db)
- [MCP tips, tricks and pitfalls - Nearform](https://nearform.com/digital-community/implementing-model-context-protocol-mcp-tips-tricks-and-pitfalls/)
- [MCP error handling and debugging](https://www.stainless.com/mcp/error-handling-and-debugging-mcp-servers)
- Project CONCERNS.md analysis (2026-03-09)

---
*Pitfalls research for: Python MCP server wrapping Logseq HTTP API*
*Researched: 2026-03-09*
