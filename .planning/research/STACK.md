# v1.1 Stack Research

## Scope

Research for `journal_today`, `journal_append`, `journal_range`, `delete_page`, `rename_page`, and `move_block`.

## Existing Stack To Reuse

- Python 3.12+
- FastMCP
- `httpx.AsyncClient`
- Pydantic v2
- pytest
- uv
- Logseq HTTP API over `POST /api`

## Required Stack and API Considerations

- Keep all requests inside the existing single-flight client pattern. Do not add parallel Logseq RPC fan-out for journal ranges or move operations.
- Keep writes and reads stateless. Logseq remains the source of truth; no local cache or journal registry should be introduced.
- Use existing Logseq RPC surface for lifecycle writes: `deletePage`, `renamePage`, `moveBlock`, `getPage`, `getPageBlocksTree`, and `getBlock`.
- `journal_today` and `journal_append` should compose existing page lookup/create and block append behavior instead of inventing a second write path.
- `journal_range` may need a constrained internal `datascriptQuery` path to resolve journals by `journal-day` metadata without exposing a general query tool in `v1.1`.
- Reuse existing `PageEntity` journal fields (`journal`, `journal_day`) instead of adding a second journal-specific page model.
- Define `move_block` positions explicitly at the tool boundary. Support `before`, `after`, and `child`; do not leak raw Logseq option dicts to callers.

## Testing and Runtime Implications

- Live Logseq integration remains mandatory because these tools depend on real graph state and Logseq mutation semantics.
- Extend the existing readback verification pattern:
  - `journal_today`: fetched or created page must come back as a journal page.
  - `journal_append`: appended content must appear on the target journal page.
  - `journal_range`: range filtering must track actual journal metadata, not just guessed names.
  - `delete_page`: page must no longer resolve after deletion.
  - `rename_page`: old name must disappear and new name must resolve.
  - `move_block`: moved subtree must appear at destination and disappear from the source location.
- Keep MCP-native error normalization and stderr-only logging behavior.

## Explicit Non-Goals For v1.1

- No general DataScript query tools (`query`, `find_by_tag`, `query_properties`)
- No template, kanban, or search features
- No cache, background sync, or local graph state
- No transport changes or multi-backend work
