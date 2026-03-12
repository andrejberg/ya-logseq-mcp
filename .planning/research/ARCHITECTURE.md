# v1.1 Architecture Research

## Modified Components

- `src/logseq_mcp/server.py`
  Register the six new tools.
- `src/logseq_mcp/tools/write.py`
  Extend shared mutation helpers and implement `delete_page`, `rename_page`, and `move_block`.
- `src/logseq_mcp/client.py`
  Keep single-flight `_call()` behavior and add wrappers only if they reduce repeated tool logic.
- `tests/test_write.py`
  Add lifecycle mutation unit coverage.
- `tests/test_server.py`
  Expand tool registry expectations.
- `tests/integration/test_mcp_stdio.py`
  Expand required tool exposure and stdio round trips.
- `tests/integration/test_live_graph.py`
  Add isolated live coverage for lifecycle and journal flows.

## New Components

- `src/logseq_mcp/tools/journal.py`
  Owns date parsing, journal lookup/create, and journal read/write tools.
- `tests/test_journal.py`
  Unit coverage for journal-specific behavior.

## Integration Guidance

- Keep the current flow: `FastMCP tool -> AppContext.client -> Logseq RPC -> typed validation/readback -> JSON result`.
- `journal_today` should resolve or create a journal page, then return page metadata plus block tree in the same shape as `get_page`.
- `journal_append` should reuse the existing block normalization and append tree helpers from `write.py`.
- `journal_range` should come after the journal date-resolution rules are settled. Prefer stable journal metadata over page-name guessing.
- `delete_page`, `rename_page`, and `move_block` should all follow the existing mutate-then-readback verification contract.

## Suggested Build Order

1. Shared write verification helpers and lifecycle tool tests
2. `delete_page`, `rename_page`, and `move_block`
3. Server and stdio registration updates
4. `journal.py` and `journal_today`
5. `journal_append` on top of shared append logic
6. `journal_range` once journal lookup behavior is stable
7. Live isolated-graph integration coverage
