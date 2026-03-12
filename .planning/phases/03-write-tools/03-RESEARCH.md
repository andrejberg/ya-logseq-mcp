# Phase 3: Write Tools - Research

**Researched:** 2026-03-09
**Domain:** Logseq HTTP API write operations, hierarchy-safe block insertion, write verification
**Confidence:** MEDIUM-HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| WRIT-01 | `page_create` creates a page with properties and optional initial blocks | Plan around `logseq.Editor.createPage(name, properties, opts)` plus read-after-write verification because page-vs-block property behavior is subtle |
| WRIT-02 | `block_append` appends blocks to a page, accepting both flat strings and nested `{content, properties, children}` objects | Normalize all inputs into one recursive write model before any API calls |
| WRIT-03 | `block_append` produces correct Logseq block hierarchy | Use sequential root append + recursive child inserts; verify with `getPageBlocksTree`, not only raw write responses |
| WRIT-04 | `block_update` updates block content by UUID | `logseq.Editor.updateBlock(uuid, content, ...)` should be followed by read-back verification |
| WRIT-05 | `block_delete` deletes a block by UUID | `logseq.Editor.removeBlock(uuid)` must be treated as successful only if later reads no longer return the block |
</phase_requirements>

---

## Summary

Phase 3 should stay narrow: deliver `page_create`, `block_append`, `block_update`, and `block_delete` from the v1 requirements, even though `CLAUDE.md` lists additional write tools in the eventual `write.py` module. The main planning risk is not transport or registration; those patterns are already established. The main risk is write correctness in Logseq's underdocumented API, especially page properties vs block properties and preserving child order in nested inserts.

The safest implementation shape is a dedicated `src/logseq_mcp/tools/write.py` module that mirrors `tools/core.py`: thin `@mcp.tool()` handlers, `client._call(...)`, explicit `McpError` on missing targets, and JSON string returns. Add only the input models needed to normalize nested write payloads. Do not default to batch insertion. Prior project research already flags `insertBatchBlock` as risky, and the client's semaphore means sequential writes are acceptable for this scope.

The planner should assume this phase needs both unit tests and live integration validation. Unit tests can prove call sequencing and normalization. They cannot prove that page properties appear correctly in Logseq's UI or that nested children land in the intended hierarchy. Those behaviors need read-after-write checks against a real Logseq graph.

---

## Implementation Constraints

- Preserve the existing server pattern: tools return JSON strings, use `AppContext` from `ctx.request_context.lifespan_context`, and rely on `client._call(...)`.
- Keep all write traffic serialized through the existing `asyncio.Semaphore(1)` in [`client.py`](/home/berga/Workspace/projects/logseq-mcp/src/logseq_mcp/client.py). Do not add local concurrency inside nested append helpers.
- Register a new `write` module from [`server.py`](/home/berga/Workspace/projects/logseq-mcp/src/logseq_mcp/server.py) the same way `core` is registered today.
- Prefer a write-specific recursive input model over reusing `BlockEntity`. Read models describe API output; Phase 3 needs a stricter input contract with required `content`, optional `properties`, and recursive `children`.
- Fail before partial mutation when payload shape is invalid. Normalize the full tree first, then execute writes.
- Use page-tree reads for hierarchy verification. [`types.py`](/home/berga/Workspace/projects/logseq-mcp/src/logseq_mcp/types.py) intentionally drops compact child refs from `getBlock`, so `getBlock(..., includeChildren=True)` is not sufficient to prove full nesting.
- Treat `CLAUDE.md`'s extra write tools as out of scope for planning unless the roadmap is updated. The traceable Phase 3 requirements are only WRIT-01 through WRIT-05.

---

## Likely API Calls

| Tool | Likely RPC | Planning Notes |
|------|------------|----------------|
| `page_create` | `logseq.Editor.createPage(name, properties, opts)` | Verify exact opts needed for `createFirstBlock`; success depends on properties surfacing as page properties in Logseq UI |
| `block_append` root blocks | `logseq.Editor.appendBlockInPage(page_name, content, opts)` | Use for top-level blocks in the requested order |
| `block_append` child blocks | `logseq.Editor.insertBlock(parent_uuid, content, opts)` | Most likely `sibling: false` for child insertion; exact option shape should be confirmed in live testing before final plan lock |
| `block_update` | `logseq.Editor.updateBlock(uuid, content, opts?)` | Treat as incomplete until read-back confirms content changed |
| `block_delete` | `logseq.Editor.removeBlock(uuid)` | Verify absence via read after deletion |
| verification reads | `logseq.Editor.getPage`, `logseq.Editor.getPageBlocksTree`, `logseq.Editor.getBlock` | Reuse Phase 2 read paths for state validation |

### Call-Signature Uncertainties To Resolve Early

- Whether `createPage(..., properties, opts)` alone is sufficient for properties to appear in Logseq's page-properties UI on the target Logseq version.
- The exact `insertBlock` option shape required to force child insertion without reversing sibling order.
- Whether `removeBlock` cascades children the way Phase 3 expects, or whether tests must only assert the target block disappears.
- Whether `appendBlockInPage` should be allowed to create missing pages implicitly, or whether the tool should preflight with `getPage` and fail if absent.

These are planning blockers for integration tests, not for unit-test scaffolding.

---

## Recommended Architecture Patterns

### Pattern 1: Dedicated write normalization

Normalize inputs up front into one recursive model, for example:

- string input -> `{content: <string>, properties: {}, children: []}`
- object input -> validated recursive node
- list input -> normalized list preserving caller order

This avoids mixing parsing and mutation logic and gives the planner a clean split between "validate tree" and "execute tree".

### Pattern 2: Sequential recursive insertion

- Append each top-level node to the page in order.
- Capture the returned UUID for each created block.
- Insert children recursively under the created parent before moving to the next sibling only if that preserves order in Logseq.
- If child insertion order proves reversed in practice, adjust the algorithm before broad implementation rather than patching per depth.

This is slower than batching, but Phase 1 already optimized for correctness over throughput.

### Pattern 3: Shared write verification helpers

A small internal helper layer in `tools/write.py` is justified:

- `_normalize_blocks(...)`
- `_append_tree_to_page(...)`
- `_insert_children(...)`
- `_verify_page_properties(...)`
- `_verify_block_absent(...)`

The planner should not duplicate read-after-write logic across four public tools.

---

## Edge Cases That Matter For Planning

### Properties

- Page properties and block properties are different systems in Logseq.
- `page_create` must put page properties at page level, not inside the first block unless live validation proves that is required for the installed Logseq build.
- `block_append` should only ever write block-level properties.
- Empty property dicts should be treated as no-op, not serialized into strange API shapes.

### Hierarchy and ordering

- Mixed flat and nested input must preserve caller order exactly.
- Child order is easy to reverse accidentally when repeatedly inserting relative to the same parent.
- A malformed child tree must fail before any writes occur; partial trees are hard to recover from.
- Verification should inspect the page tree, not rely only on the UUIDs returned by write calls.

### Existence and failure semantics

- Decide early whether `block_append` requires an existing page.
- `block_update` and `block_delete` should raise explicit `McpError` for missing UUIDs, matching Phase 2's read-tool behavior.
- If a write RPC returns `None` or an unexpected shape, treat it as failure even if no HTTP error occurred.

---

## Test Strategy

### Unit tests

Add `tests/test_write.py` using the same style as [`tests/test_core.py`](/home/berga/Workspace/projects/logseq-mcp/tests/test_core.py):

- import tool functions inside each test body
- mock `client._call` with `AsyncMock` or async closures
- assert JSON output and exact RPC call order

Minimum unit coverage:

- `page_create` passes properties as the second `createPage` arg, not buried in opts
- `page_create` appends initial blocks only after page creation succeeds
- `block_append` accepts strings and nested objects in one payload
- `block_append` emits the expected root/child write sequence
- `block_append` preserves sibling order in the generated call plan
- `block_update` calls `updateBlock` with the requested UUID and content
- `block_delete` calls `removeBlock` and reports success cleanly
- invalid nested payloads fail before the first write RPC
- missing page or missing block surfaces as `McpError`

### Integration tests

Phase 3 should introduce live-graph integration checks even if the full isolated test graph lands in Phase 4. At minimum, the planner should reserve room for manual or scripted verification of:

1. create page with properties, then verify properties in `getPage` and in Logseq UI
2. append nested blocks, then verify exact tree shape with `get_page`
3. update a block, then verify new content through `get_page` or `get_block`
4. delete a block, then verify it no longer appears in `get_page`

Without these checks, WRIT-01 and WRIT-03 can appear green in unit tests while still failing in Logseq itself.

---

## Validation Architecture

The orchestrator should generate `VALIDATION.md` around three validation layers for every write task:

### 1. Input validation

- recursive payload normalization succeeds
- invalid node shape fails before any RPC
- property maps are dict-like and content is non-empty string where required

### 2. Execution validation

- each expected RPC is called in deterministic order
- each write result is checked for `None` or malformed response
- no partial-write path is silently swallowed

### 3. State validation

- `page_create`: created page exists and properties materialize at page level
- `block_append`: read-back page tree matches requested parent/child structure and sibling order
- `block_update`: read-back block content matches the new content
- `block_delete`: target UUID is absent from subsequent reads

### Recommended validation split

- Wave 0: `tests/test_write.py` red-state stubs for WRIT-01 through WRIT-05
- Wave 1: input normalization and `page_create` unit validation
- Wave 2: nested `block_append` call sequencing and hierarchy validation
- Wave 3: `block_update`, `block_delete`, module registration, and live read-after-write checks

### Nyquist-critical checks

- No three consecutive tasks without an automated test command
- Every public write tool has at least one state-validation step, not only call-sequence assertions
- At least one validation step exercises page properties and one exercises nested children

---

## Planning Recommendations

- Split Phase 3 by risk, not by file count: normalization first, then page creation, then nested append, then update/delete plus registration.
- Keep `insertBatchBlock` out of the initial plan unless live research proves it is reliable in the target Logseq version.
- Treat property visibility in the Logseq UI as the highest-risk success criterion and schedule it for the earliest integration check.
- Reuse Phase 2 read tools as verification primitives instead of adding separate verification RPC wrappers.
