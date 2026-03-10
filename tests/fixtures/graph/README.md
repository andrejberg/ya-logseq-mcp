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

## Reset Rules

- Live write tests must fail before the first mutation if the active graph is not `logseq-test-graph`.
- Live write tests may mutate only `Phase 04 Write Sandbox`.
- Re-running the suite resets the sandbox page back to the baseline blocks before destructive assertions begin.
