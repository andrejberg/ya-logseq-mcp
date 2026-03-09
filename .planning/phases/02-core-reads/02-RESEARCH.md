# Phase 2: Core Reads - Research

**Researched:** 2026-03-09
**Domain:** Logseq HTTP API read operations, block tree deduplication, FastMCP tool patterns
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| READ-01 | `get_page` returns page metadata and block tree deduplicated by UUID | `getPageBlocksTree` returns full nested `BlockEntity` objects; deduplicate by tracking seen UUIDs during recursive traversal |
| READ-02 | `get_page` preserves correct parent/child nesting (no blocks promoted to wrong level) | Nesting is already encoded in the `children` array of `BlockEntity`; the duplication bug in graphthulhu was from recursive traversal double-counting, NOT from wrong nesting — just collect by children list, do not re-walk parents |
| READ-03 | `get_page` uses page name (not UUID) for `getPageBlocksTree` calls | Confirmed: `getPageBlocksTree` accepts page name string; the `getPage` call also uses name |
| READ-04 | `get_block` returns a single block by UUID with optional children | `getBlock(uuid, {"includeChildren": true})` — opts dict as second arg; children come back as compact `[["uuid","val"]]` from this call (handled by existing `handle_compact_children` validator — children will be `[]`) |
| READ-05 | `list_pages` returns pages with optional namespace filter | `getAllPages` returns all pages; filter in Python by `name.startswith(namespace.lower())` |
| READ-06 | `get_references` returns backlinks to a page via `getPageLinkedReferences` | `getPageLinkedReferences(page_name)` returns `[[PageEntity, [BlockEntity, ...]], ...]` — parse as list of `[page, blocks]` pairs |
</phase_requirements>

---

## Summary

Phase 2 implements four read tools — `get_page`, `get_block`, `list_pages`, and `get_references` — on top of the async `LogseqClient` built in Phase 1. The primary challenge and the reason this project exists is the block-duplication bug in graphthulhu: `getPageBlocksTree` returns a correctly nested tree where each block appears once, but graphthulhu's `enrichBlockTree` recursively re-walks the children it has already placed, causing 4-8x duplication. The fix is simple: traverse the tree returned by `getPageBlocksTree` without re-walking nodes — just recursively process the `children` array of each block.

The other three tools are straightforward wrappers: `get_block` calls `getBlock` with `{"includeChildren": true}`, `list_pages` calls `getAllPages` and filters in Python, and `get_references` calls `getPageLinkedReferences` and parses its unusual `[[page, [blocks]], ...]` response shape.

All four tools follow the pattern established by the `health` tool: `@mcp.tool()` decorator, `ctx: Context` first argument, `client = ctx.request_context.lifespan_context.client`, return JSON string. No new dependencies are needed. Tests follow the mock-transport + `AsyncMock` pattern from Phase 1.

**Primary recommendation:** Implement all four tools in `tools/core.py` as a single wave — they share no dependencies on each other and the file is already the target module. Deduplication is the key correctness requirement; write a test that constructs a tree with repeated UUIDs and asserts none appear in output.

---

## Standard Stack

### Core (no changes from Phase 1)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| mcp (FastMCP) | 1.26.0 | Tool registration, stdio transport | Already locked in uv.lock |
| httpx | 0.28.1 | Async HTTP client for Logseq API | Already locked |
| pydantic | 2.12.5 | `BlockEntity`, `PageEntity` parsing | Already locked; `BlockEntity.children` handles nesting |
| asyncio | stdlib | Semaphore serialization | Already in client |

### Dev / Test
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | 9.0.2 | Test runner | All tests |
| pytest-asyncio | 1.3.0 | async test support | All `async def test_*` |

**No new dependencies for Phase 2.** `uv sync` is sufficient.

---

## Architecture Patterns

### Recommended Project Structure (after Phase 2)
```
src/logseq_mcp/
├── __init__.py
├── __main__.py
├── server.py          # FastMCP instance, lifespan, imports tools/core
├── client.py          # LogseqClient._call() — unchanged from Phase 1
├── types.py           # BlockEntity, PageEntity — unchanged from Phase 1
└── tools/
    ├── __init__.py    # (empty)
    └── core.py        # health (existing) + get_page, get_block, list_pages, get_references
tests/
├── conftest.py        # shared fixtures (token_env, logseq_200, mock_transport)
├── test_client.py     # Phase 1 tests (unchanged)
├── test_types.py      # Phase 1 tests (unchanged)
├── test_server.py     # Phase 1 tests (unchanged)
└── test_core.py       # NEW — Phase 2 tool tests
```

### Pattern 1: Tool Handler Structure
All tool handlers follow the same pattern established by `health`:

```python
# tools/core.py
@mcp.tool()
async def get_page(ctx: Context, name: str) -> str:
    """Get a page and its block tree, deduplicated by UUID."""
    app_ctx: AppContext = ctx.request_context.lifespan_context
    client = app_ctx.client
    logger.info("get_page: %s", name)

    page_raw = await client._call("logseq.Editor.getPage", name)
    if page_raw is None:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"page not found: {name}"))

    page = PageEntity.model_validate(page_raw)

    blocks_raw = await client._call("logseq.Editor.getPageBlocksTree", name)
    blocks_list = blocks_raw if isinstance(blocks_raw, list) else []

    # Deduplicate by UUID during parse
    blocks = _parse_block_tree(blocks_list)

    result = {
        "page": page.model_dump(by_alias=False),
        "blocks": [b.model_dump(by_alias=False) for b in blocks],
        "block_count": _count_blocks(blocks),
    }
    return json.dumps(result)
```

### Pattern 2: Block Tree Deduplication (the core fix)

The graphthulhu bug: `enrichBlockTree` is called recursively, and each call re-processes children that are already embedded in parent nodes. This causes blocks to appear multiple times.

The fix: parse each `BlockEntity` once using `BlockEntity.model_validate()`. Because `BlockEntity.children` is already a recursive `list["BlockEntity"]`, Pydantic parses the entire tree in one call with no double-counting. The only additional step is UUID deduplication to guard against edge cases:

```python
def _parse_block_tree(raw_blocks: list) -> list[BlockEntity]:
    """Parse raw block dicts into BlockEntity objects, deduped by UUID."""
    seen: set[str] = set()
    result: list[BlockEntity] = []
    for raw in raw_blocks:
        block = BlockEntity.model_validate(raw)
        if block.uuid and block.uuid in seen:
            continue  # skip genuine duplicate
        if block.uuid:
            seen.add(block.uuid)
        block.children = _dedup_children(block.children, seen)
        result.append(block)
    return result


def _dedup_children(children: list[BlockEntity], seen: set[str]) -> list[BlockEntity]:
    """Recursively remove children with already-seen UUIDs."""
    result: list[BlockEntity] = []
    for child in children:
        if child.uuid and child.uuid in seen:
            continue
        if child.uuid:
            seen.add(child.uuid)
        child.children = _dedup_children(child.children, seen)
        result.append(child)
    return result
```

**Key insight:** `BlockEntity.model_validate(raw)` already recursively parses all children via the Pydantic model — the tree arrives correctly nested from the API. Deduplication is a UUID-set pass, not a structural restructuring.

### Pattern 3: `get_block` — opts dict as second arg

```python
@mcp.tool()
async def get_block(ctx: Context, uuid: str, include_children: bool = True) -> str:
    """Get a single block by UUID."""
    app_ctx: AppContext = ctx.request_context.lifespan_context
    client = app_ctx.client
    logger.info("get_block: %s", uuid)

    opts = {"includeChildren": include_children}
    raw = await client._call("logseq.Editor.getBlock", uuid, opts)
    if raw is None:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"block not found: {uuid}"))

    block = BlockEntity.model_validate(raw)
    # Note: children from getBlock are compact [["uuid","val"]] — already handled
    # by handle_compact_children validator, so block.children will be []
    return json.dumps(block.model_dump(by_alias=False))
```

**Important:** `getBlock` with `includeChildren: true` returns children in compact format `[["uuid", "val"]]`. The existing `handle_compact_children` validator in `BlockEntity` already converts this to `children=[]`. This is correct and expected — the single-block call does not deliver a usable child tree. To get children of a block, the consumer should use `get_page` and navigate the tree.

### Pattern 4: `list_pages` — filter in Python

```python
@mcp.tool()
async def list_pages(
    ctx: Context,
    namespace: str = "",
    include_journals: bool = False,
    limit: int = 50,
) -> str:
    """List pages with optional namespace filter."""
    app_ctx: AppContext = ctx.request_context.lifespan_context
    client = app_ctx.client
    logger.info("list_pages: namespace=%r limit=%d", namespace, limit)

    raw = await client._call("logseq.Editor.getAllPages")
    pages_raw = raw if isinstance(raw, list) else []

    pages: list[PageEntity] = []
    for p in pages_raw:
        page = PageEntity.model_validate(p)
        if not page.name:
            continue
        if not include_journals and page.journal:
            continue
        if namespace and not page.name.lower().startswith(namespace.lower()):
            continue
        pages.append(page)

    pages.sort(key=lambda p: p.name.lower())
    if limit > 0:
        pages = pages[:limit]

    result = [
        {"name": p.original_name or p.name, "journal": p.journal, "properties": p.properties}
        for p in pages
    ]
    return json.dumps(result)
```

**Note on namespace API:** Logseq has `getPagesFromNamespace(namespace)` but graphthulhu uses `getAllPages` + Python filter. Using `getAllPages` + filter is simpler and avoids a second API discovery. It is an acceptable approach for the page counts in a personal graph (typically hundreds, not millions).

### Pattern 5: `get_references` — parse `[[page, [blocks]], ...]` response

`getPageLinkedReferences` returns a list of `[page_dict, [block_dict, ...]]` pairs. This is an unusual shape — not a list of objects, but a list of two-element arrays.

```python
@mcp.tool()
async def get_references(ctx: Context, name: str) -> str:
    """Get backlinks to a page."""
    app_ctx: AppContext = ctx.request_context.lifespan_context
    client = app_ctx.client
    logger.info("get_references: %s", name)

    raw = await client._call("logseq.Editor.getPageLinkedReferences", name)
    if not isinstance(raw, list):
        return json.dumps([])

    backlinks = []
    for ref in raw:
        if not isinstance(ref, list) or len(ref) < 2:
            continue
        page_raw, blocks_raw = ref[0], ref[1]
        try:
            page = PageEntity.model_validate(page_raw)
            blocks = [BlockEntity.model_validate(b) for b in (blocks_raw or [])]
        except Exception:
            continue
        backlinks.append({
            "page": page.original_name or page.name,
            "blocks": [
                {"uuid": b.uuid, "content": b.content}
                for b in blocks
            ],
        })

    return json.dumps(backlinks)
```

### Pattern 6: Logseq API — exact call signatures (verified from graphthulhu/client/logseq.go)

| Tool | API Method | Args | Returns |
|------|-----------|------|---------|
| `get_page` | `logseq.Editor.getPage` | `[name]` | `PageEntity` dict or `null` |
| `get_page` (blocks) | `logseq.Editor.getPageBlocksTree` | `[name]` | `[BlockEntity, ...]` or `null` |
| `get_block` | `logseq.Editor.getBlock` | `[uuid, {"includeChildren": true}]` | `BlockEntity` dict or `null` |
| `list_pages` | `logseq.Editor.getAllPages` | `[]` | `[PageEntity, ...]` |
| `get_references` | `logseq.Editor.getPageLinkedReferences` | `[name]` | `[[page, [blocks]], ...]` |

**Confirmed:** All four methods use page **name** (string), not UUID, as the identifier. `getPageBlocksTree` takes the page name, same as `getPage`. READ-03 is satisfied by passing `name` directly.

### Pattern 7: `_count_blocks` helper

```python
def _count_blocks(blocks: list[BlockEntity]) -> int:
    count = len(blocks)
    for b in blocks:
        count += _count_blocks(b.children)
    return count
```

### Anti-Patterns to Avoid

- **Re-enriching already-parsed children:** graphthulhu calls `enrichBlockTree(b.BlockEntity.Children, ...)` inside the loop that also processes top-level blocks — this double-counts every subtree. Never re-walk children that are already embedded.
- **Using `getBlock` to get a child tree:** `getBlock(uuid, {includeChildren: true})` returns compact `[["uuid","val"]]` children, which the model converts to `[]`. Use `get_page` + tree traversal for child access.
- **Filtering journals with `journal?` string comparison:** The `PageEntity.journal` field is a bool parsed from `"journal?"` key. Use `page.journal` (bool), not string comparison.
- **Passing `None` through `model_dump`:** Call `page.model_dump(by_alias=False)` to get snake_case keys; `by_alias=True` gives kebab-case (e.g. `original-name`) which is harder to consume.
- **Returning raw Logseq dicts:** Always parse through Pydantic then re-serialize — this ensures consistent shape regardless of API quirks.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Block tree parsing | Custom recursive dict walker | `BlockEntity.model_validate(raw)` | Pydantic handles full recursive parse of children in one call |
| Namespace filtering | `getPagesFromNamespace` API call | `getAllPages` + Python filter | Simpler, no extra API discovery, same result for personal graphs |
| Backlink parsing | Custom JSON parser | `PageEntity.model_validate()` + `BlockEntity.model_validate()` | Existing models handle the shapes; just handle the `[[page, blocks]]` outer structure |
| UUID deduplication | Complex tree restructuring | Set-based UUID tracking in one pass | The tree is already correctly structured; just skip repeats |

---

## Common Pitfalls

### Pitfall 1: Mistaking Enrichment Re-walk for Nesting Bug
**What goes wrong:** The graphthulhu duplication is caused by `enrichBlockTree` re-walking children that are already embedded inside parent `BlockEntity.Children`. It is NOT a nesting-level problem (blocks at the wrong depth).
**Why it happens:** The enrichment function is called recursively at each level AND called on already-embedded children.
**How to avoid:** Call `BlockEntity.model_validate(raw)` once per top-level block. The resulting tree is already correctly nested. Only deduplicate; do not restructure.
**Warning signs:** Seeing the same UUID multiple times in output at different nesting depths.

### Pitfall 2: `getPageBlocksTree` Returns `null` for Non-Existent Pages
**What goes wrong:** Calling `getPageBlocksTree` on a page that doesn't exist returns `null` (Python `None`). `isinstance(None, list)` is `False` — safe to check.
**Why it happens:** Logseq API returns `null` for many "not found" cases.
**How to avoid:** Always guard: `blocks_list = raw if isinstance(raw, list) else []`. Never call `len(raw)` without checking type.
**Warning signs:** `TypeError: object of type 'NoneType' has no len()`.

### Pitfall 3: `getPage` Returns `null` for Non-Existent Pages
**What goes wrong:** `await client._call("logseq.Editor.getPage", name)` returns `None` when page doesn't exist. Passing `None` to `PageEntity.model_validate()` raises `ValidationError`.
**Why it happens:** Logseq HTTP API returns JSON `null` for missing pages.
**How to avoid:** Check `if page_raw is None: raise McpError(...)` before validating.
**Warning signs:** `pydantic.ValidationError: 1 validation error for PageEntity` with input `None`.

### Pitfall 4: `getAllPages` Includes Pages With Empty Names
**What goes wrong:** The `getAllPages` response includes some internal/system pages with `name: ""`. Passing these through produces empty-name entries in the tool output.
**Why it happens:** Logseq's internal graph metadata appears as "pages" in the API.
**How to avoid:** Filter: `if not page.name: continue` in `list_pages`.
**Warning signs:** Empty strings in `list_pages` output.

### Pitfall 5: `getPageLinkedReferences` Returns `null` When No Backlinks
**What goes wrong:** Returns `null` (not empty list `[]`) when the page has no backlinks. Iterating over `None` raises `TypeError`.
**Why it happens:** Logseq API inconsistency — empty collections sometimes return `null`.
**How to avoid:** `if not isinstance(raw, list): return json.dumps([])`.
**Warning signs:** `TypeError: 'NoneType' object is not iterable`.

### Pitfall 6: `model_dump(by_alias=True)` Produces Kebab-Case Keys
**What goes wrong:** `PageEntity` has `original_name: str = Field("", alias="original-name")`. Calling `model_dump(by_alias=True)` produces `{"original-name": ...}` instead of `{"original_name": ...}`.
**Why it happens:** Pydantic uses the alias when `by_alias=True`.
**How to avoid:** Always use `model_dump(by_alias=False)` for tool output.
**Warning signs:** Tool output keys with hyphens (`"original-name"`, `"pre-block"`, `"path-refs"`).

---

## Code Examples

### Minimal get_page skeleton (verified patterns)
```python
# Source: pattern from tools/core.py health + graphthulhu/client/logseq.go GetPage/GetPageBlocksTree
import json
import logging
from mcp import McpError
from mcp.types import ErrorData, INTERNAL_ERROR
from mcp.server.fastmcp import Context

from logseq_mcp.server import mcp, AppContext
from logseq_mcp.types import BlockEntity, PageEntity

logger = logging.getLogger(__name__)

@mcp.tool()
async def get_page(ctx: Context, name: str) -> str:
    """Get a page and its deduplicated block tree by page name."""
    app_ctx: AppContext = ctx.request_context.lifespan_context
    client = app_ctx.client

    page_raw = await client._call("logseq.Editor.getPage", name)
    if page_raw is None:
        raise McpError(ErrorData(code=INTERNAL_ERROR, message=f"page not found: {name}"))
    page = PageEntity.model_validate(page_raw)

    blocks_raw = await client._call("logseq.Editor.getPageBlocksTree", name)
    blocks = _parse_block_tree(blocks_raw if isinstance(blocks_raw, list) else [])

    return json.dumps({
        "page": page.model_dump(by_alias=False),
        "blocks": [b.model_dump(by_alias=False) for b in blocks],
        "block_count": _count_blocks(blocks),
    })
```

### Deduplication with seen-set (verified logic)
```python
# Source: derived from graphthulhu bug analysis; see navigate.go enrichBlockTree
def _parse_block_tree(raw_blocks: list) -> list[BlockEntity]:
    seen: set[str] = set()
    result: list[BlockEntity] = []
    for raw in raw_blocks:
        block = BlockEntity.model_validate(raw)
        if block.uuid and block.uuid in seen:
            continue
        if block.uuid:
            seen.add(block.uuid)
        block.children = _dedup_children(block.children, seen)
        result.append(block)
    return result

def _dedup_children(children: list[BlockEntity], seen: set[str]) -> list[BlockEntity]:
    result: list[BlockEntity] = []
    for child in children:
        if child.uuid and child.uuid in seen:
            continue
        if child.uuid:
            seen.add(child.uuid)
        child.children = _dedup_children(child.children, seen)
        result.append(child)
    return result
```

### Test pattern for tool with mocked client (verified from test_server.py)
```python
# Source: test_server.py test_health_returns_json — same mock pattern
import pytest
from unittest.mock import AsyncMock

async def fake_call(method, *args):
    if method == "logseq.Editor.getPage":
        return {"id": 1, "uuid": "page-uuid", "name": "test-page", "original-name": "Test Page"}
    if method == "logseq.Editor.getPageBlocksTree":
        return [
            {"uuid": "block-1", "content": "Hello", "children": []},
            {"uuid": "block-2", "content": "World", "children": []},
        ]
    return None

@pytest.mark.asyncio
async def test_get_page_returns_correct_structure(token_env):
    from logseq_mcp.tools.core import get_page
    from logseq_mcp.server import AppContext
    mock_client = AsyncMock()
    mock_client._call = fake_call
    mock_ctx = AsyncMock()
    mock_ctx.request_context.lifespan_context = AppContext(client=mock_client)
    result = json.loads(await get_page(mock_ctx, "test-page"))
    assert result["page"]["name"] == "test-page"
    assert result["block_count"] == 2
```

### Deduplication test pattern
```python
# Validates READ-01: zero duplicate UUIDs in output
@pytest.mark.asyncio
async def test_get_page_deduplicates_blocks(token_env):
    # Simulate graphthulhu-style duplication: block appears at top level AND as child
    duplicated_raw = [
        {"uuid": "A", "content": "Parent", "children": [
            {"uuid": "B", "content": "Child", "children": []}
        ]},
        {"uuid": "B", "content": "Child (duplicate)", "children": []},  # B appears again
    ]
    # ... mock client to return duplicated_raw from getPageBlocksTree
    # ... call get_page, parse result
    # assert no duplicate UUIDs
    all_uuids = collect_all_uuids_from_result(result["blocks"])
    assert len(all_uuids) == len(set(all_uuids))  # no duplicates
```

---

## State of the Art

| Old Approach (graphthulhu) | Current Approach | Impact |
|---------------------------|------------------|--------|
| `enrichBlockTree` re-walks embedded children | `model_validate` once + UUID dedup pass | Eliminates 4-8x block duplication |
| `compact: true` parameter (doesn't fix duplication) | No compact mode; lean output by default | Simpler API, correct output |
| `getLinks` tool with BFS traversal | Not implemented (v2 scope) | Out of scope; `query` DataScript covers it |
| `GetReferences` uses DataScript query on block UUID | `getPageLinkedReferences` by page name | Different API — ours returns page-level backlinks, not block-level refs |

**Deprecated/outdated:**
- `enrichBlockTree` from graphthulhu: causes the duplication; do not replicate this pattern
- `compact: true` parameter: does not fix duplication in graphthulhu; not implemented here

---

## Open Questions

1. **`getPageLinkedReferences` response shape on empty graph**
   - What we know: Graphthulhu treats it as `[[PageEntity, [BlockEntity, ...]], ...]`
   - What's unclear: Whether it returns `null`, `[]`, or `[[]]` when there are no backlinks
   - Recommendation: Guard with `if not isinstance(raw, list): return json.dumps([])` covers all cases

2. **`getAllPages` performance on large graphs**
   - What we know: Fetches ALL pages, then filters in Python
   - What's unclear: Whether `getPagesFromNamespace` would be faster for namespace-filtered calls
   - Recommendation: Start with `getAllPages` (simpler); if performance becomes an issue in v2, add `getPagesFromNamespace` as an optimization path

3. **`pre_block` field semantics**
   - What we know: `pre_block` (alias `"pre-block?"`) is a bool in `BlockEntity`; graphthulhu has it
   - What's unclear: Whether pre-block (page properties block) should be included or excluded from `get_page` output
   - Recommendation: Include it by default; it contains page-level properties that are useful

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 + pytest-asyncio 1.3.0 |
| Config file | `pyproject.toml` — `[tool.pytest.ini_options]` asyncio_mode = "auto" (already set) |
| Quick run command | `uv run pytest tests/ -x -q` |
| Full suite command | `uv run pytest tests/ -v` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| READ-01 | `get_page` output has zero duplicate UUIDs | unit | `uv run pytest tests/test_core.py::test_get_page_no_duplicate_uuids -x` | ❌ Wave 0 |
| READ-02 | `get_page` preserves correct parent/child nesting | unit | `uv run pytest tests/test_core.py::test_get_page_nesting_correct -x` | ❌ Wave 0 |
| READ-03 | `get_page` passes page name (not UUID) to `getPageBlocksTree` | unit | `uv run pytest tests/test_core.py::test_get_page_uses_name -x` | ❌ Wave 0 |
| READ-04 | `get_block` returns block by UUID; children=[] (compact format) | unit | `uv run pytest tests/test_core.py::test_get_block_returns_block -x` | ❌ Wave 0 |
| READ-05 | `list_pages` filters by namespace | unit | `uv run pytest tests/test_core.py::test_list_pages_namespace_filter -x` | ❌ Wave 0 |
| READ-06 | `get_references` parses `[[page, blocks]]` into backlinks list | unit | `uv run pytest tests/test_core.py::test_get_references_parses_response -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/ -x -q`
- **Per wave merge:** `uv run pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_core.py` — covers READ-01 through READ-06; new file required before implementation
- [ ] All existing test files remain valid; no changes to `test_client.py`, `test_types.py`, `test_server.py`

*(No framework gaps — pytest config already in place from Phase 1)*

---

## Sources

### Primary (HIGH confidence)
- `/home/berga/Workspace/projects/logseq-mcp/graphthulhu/client/logseq.go` — exact API method names, arg order, and return types for all four operations
- `/home/berga/Workspace/projects/logseq-mcp/graphthulhu/tools/navigate.go` — `GetPage`, `GetBlock`, `ListPages`, `GetLinks`/`getBacklinks` implementations; source of duplication bug analysis
- `/home/berga/Workspace/projects/logseq-mcp/graphthulhu/types/logseq.go` — `BlockEntity.UnmarshalJSON` compact-children handling; `getPageLinkedReferences` response shape
- `/home/berga/Workspace/projects/logseq-mcp/src/logseq_mcp/types.py` — existing `BlockEntity`, `PageEntity` Pydantic models; `handle_compact_children` validator
- `/home/berga/Workspace/projects/logseq-mcp/src/logseq_mcp/tools/core.py` — existing `health` tool pattern
- `/home/berga/Workspace/projects/logseq-mcp/tests/test_server.py` — existing mock-client test pattern

### Secondary (MEDIUM confidence)
- `/home/berga/Workspace/projects/logseq-mcp/.planning/REQUIREMENTS.md` — READ-01 through READ-06 requirement text
- `/home/berga/Workspace/projects/logseq-mcp/CLAUDE.md` — tool spec (get_page deduplication fix, lean default, list_pages namespace filter)

### Tertiary (LOW confidence)
- None — all findings grounded in source code

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — locked in uv.lock; no new deps; existing patterns verified in Phase 1
- Architecture: HIGH — derived directly from graphthulhu Go source + existing Phase 1 Python code
- Pitfalls: HIGH — graphthulhu bug identified from source; null-return patterns from Go implementation
- Deduplication algorithm: HIGH — derived from actual bug in `enrichBlockTree`; fix is a standard set-tracking pass
- `getPageLinkedReferences` response shape: MEDIUM — confirmed from graphthulhu's `getBacklinks` parser but not tested against live API

**Research date:** 2026-03-09
**Valid until:** 2026-06-09 (Logseq HTTP API is stable; no API version changes expected)
