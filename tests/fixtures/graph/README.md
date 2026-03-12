# Phase 4 Isolated Logseq Graph

These fixtures are only for live integration runs against a disposable Logseq graph.

## Required Graph

- Graph name: `logseq-test-graph`
- Override only if needed: `export LOGSEQ_TEST_GRAPH_NAME="your-graph-name"`
- Daily-driver graphs are forbidden targets for this test selection.

## Required Pages

- `tests/fixtures/graph/pages/parity-page.md` must exist in Logseq as `Phase 04 Parity Fixture`
- `tests/fixtures/graph/pages/write-sandbox.md` must exist in Logseq as `Phase 04 Write Sandbox`

The parity page is a deterministic nested tree for Phase 4 parity checks. The write sandbox is the only approved target for append, update, and delete verification.

## Setup

1. Create or open a disposable graph directory named `logseq-test-graph`.
2. Copy the fixture markdown files into that graph's `pages/` directory.
3. Open Logseq and switch the active graph to `logseq-test-graph`.
4. Generate or copy the API token from Logseq, then export it:

```bash
export LOGSEQ_API_TOKEN="..."
export LOGSEQ_API_URL="http://127.0.0.1:12315"
export LOGSEQ_TEST_GRAPH_NAME="logseq-test-graph"
```

5. Run only the explicit integration selection you want. Example:

```bash
uv run pytest tests/integration/test_live_graph.py -m integration -q
```

## Graphthulhu Parity Prerequisite

Phase 4 parity verification uses the shared workspace MCP config and selects the `graphthulhu` server entry by name.

1. Confirm the workspace config exists at `~/Workspace/.mcp.json`.
2. Confirm it contains both `logseq-mcp` and `graphthulhu` entries under `mcpServers`.
3. Override only if needed:

```bash
export WORKSPACE_MCP_CONFIG="$HOME/Workspace/.mcp.json"
export GRAPHTHULHU_MCP_SERVER="graphthulhu"
```

4. Keep graphthulhu available until the parity test passes:

```bash
source ~/Workspace/.env
uv run pytest tests/integration/test_graphthulhu_parity.py -x -q -m integration
```

The parity tests compare `get_page` on `Phase 04 Parity Fixture` from both servers, require zero duplicate UUIDs from `logseq-mcp`, preserve the expected child nesting, and assert that `logseq-mcp` returns equal-or-fewer blocks than graphthulhu.

## Workspace MCP Side-By-Side Validation Runbook

Run this only after the parity selection passes and while graphthulhu remains available as fallback.

1. Confirm the active workspace MCP config still contains both `logseq-mcp` and `graphthulhu`:

2. Reload MCP connections in the client you are validating if the config changed recently.
3. Run the isolated-graph smoke test explicitly against `logseq-mcp` on `logseq-test-graph`:
   - `health`
   - `get_page` for `Phase 04 Parity Fixture`
   - `list_pages`
   - one safe sandbox write on `Phase 04 Write Sandbox`
4. Switch Logseq back to the real daily-driver graph and run a read-only smoke test explicitly against `logseq-mcp`:
   - `health`
   - `get_page` on a known daily-driver note
   - `list_pages` on a namespace or baseline filter already used in daily work
5. If discovery fails or any `logseq-mcp` tool call fails, stop using `logseq-mcp`, continue with graphthulhu as fallback, and record the failing step before touching `.planning/STATE.md` or `.planning/ROADMAP.md`.

## Reset Rules

- Live write tests must fail before the first mutation if the active graph is not `logseq-test-graph`.
- Live write tests may mutate only `Phase 04 Write Sandbox`.
- Re-running the suite resets the sandbox page back to the baseline blocks before destructive assertions begin.
