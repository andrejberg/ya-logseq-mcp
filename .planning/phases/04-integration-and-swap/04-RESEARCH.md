# Phase 4: Integration and Swap - Research

**Researched:** 2026-03-10
**Domain:** MCP stdio integration, isolated Logseq graph validation, graphthulhu parity, Claude MCP config swap
**Confidence:** MEDIUM

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| INTG-01 | Server runs as MCP stdio transport via `python -m logseq_mcp` | Validate the real stdio entrypoint end-to-end, not just import-time registration; prove a client can launch the module and discover/invoke tools without stdout contamination |
| INTG-02 | Integration tests run against a local test Logseq graph (isolated from real graph) | Plan a dedicated graph fixture plus explicit environment scoping so test writes never touch the daily-driver graph |
| INTG-03 | Parity verified on `get_page` output vs graphthulhu (same page, fewer/correct blocks) | Use a fixed comparison page and compare structural facts, not byte-identical payloads, because the intended win is deduplication with correct nesting |
</phase_requirements>

---

## Summary

Phase 4 is the release gate, not another unit-test phase. The codebase already has the ingredients: [`__main__.py`](/home/berga/Workspace/projects/logseq-mcp/src/logseq_mcp/__main__.py) runs `mcp.run()`, [`server.py`](/home/berga/Workspace/projects/logseq-mcp/src/logseq_mcp/server.py) imports both tool modules, and the existing test suite proves mocked tool behavior. What is still missing is proof that the module behaves correctly when launched as an actual MCP stdio server, against a real Logseq graph, with Claude using it through MCP configuration.

The planning focus should therefore be on three things: a reproducible isolated test graph, a real stdio verification harness, and a controlled swap procedure from graphthulhu to `logseq-mcp`. Unit tests should remain in place, but they are no longer sufficient evidence for the Phase 4 success criteria. The riskiest failures here are integration failures that mocked tests cannot see: stdout contamination, process startup mismatch, wrong environment propagation, graph pollution, and parity regressions on `get_page`.

The cleanest Phase 4 split is:

1. Build reusable integration fixtures and a dedicated test graph workflow.
2. Add stdio-level MCP verification and parity checks against graphthulhu on a known page.
3. Perform the manual `~/.claude/.mcp.json` swap and record daily-driver verification.

---

## Standard Stack

### Existing stack to keep

| Library / Tool | Purpose | Phase 4 Use |
|----------------|---------|-------------|
| `mcp` / FastMCP | MCP server implementation | Keep server implementation unchanged; validate it from the outside as a subprocess |
| `pytest` | Test runner | Continue as the single test entrypoint |
| `pytest-asyncio` | async test support | Needed for async integration helpers |
| `uv` | Environment + run wrapper | Use `uv run` consistently for subprocess and test execution |
| Logseq desktop app | Real HTTP API provider | Required for isolated-graph integration validation |

### Recommended additions

| Library / Tool | Purpose | Why it helps |
|----------------|---------|--------------|
| `subprocess` / `asyncio.create_subprocess_exec` | Launch `python -m logseq_mcp` in tests | Gives direct stdio validation without depending on internal FastMCP state |
| MCP client-side session utilities from the installed `mcp` package | Drive `initialize`, `tools/list`, and `tools/call` over stdio | More trustworthy than hand-rolling JSON-RPC framing |
| Test graph fixture files under `tests/fixtures/graph/` | Stable graph contents for repeatable read and write assertions | Keeps parity and readback checks deterministic |

Do not add a second MCP framework, snapshot-test library, or custom process wrapper just for this phase.

---

## Architecture Patterns

### Pattern 1: Black-box stdio verification

Phase 4 should treat `python -m logseq_mcp` as a black box:

- launch it as a subprocess
- provide only the required env (`LOGSEQ_API_TOKEN`, optionally `LOGSEQ_API_URL`)
- speak MCP over stdin/stdout
- assert that `tools/list` exposes the expected tool set
- call at least `health`, `get_page`, and one write tool through MCP

This validates INTG-01 directly and catches transport issues that `tests/test_server.py` cannot catch today.

### Pattern 2: One isolated graph per integration run

The integration graph should be a separate Logseq graph directory with seed pages created only for tests. The plan should assume explicit operator setup because Logseq is a desktop app and the API is bound to the graph currently open in the UI. The safest approach is:

- create a dedicated graph directory such as `tests/fixtures/logseq-test-graph/`
- seed it with one parity page and one write-sandbox page
- require the operator to open that graph in Logseq before running Phase 4 integration tests
- fail fast if `health` reports the wrong graph name

This prevents accidental writes into the real workspace graph and makes INTG-02 enforceable.

### Pattern 3: Structural parity, not payload identity

`get_page` parity against graphthulhu should compare:

- page identity
- top-level block order
- recursive UUID uniqueness
- known child nesting
- total block count

Do not require the entire JSON payload to match graphthulhu byte-for-byte. The roadmap goal is to return fewer and more correct blocks, so exact output identity would reject the intended improvement.

### Pattern 4: Manual swap as a gated deployment step

The `~/.claude/.mcp.json` change is not just documentation. Treat it as a deployment step after automated validation:

- keep graphthulhu config available until parity and stdio checks pass
- add `logseq-mcp` alongside graphthulhu first if the local workflow allows two servers
- then replace the active entry once daily-driver verification passes

---

## Implementation Constraints

- Keep the Phase 4 work mostly in `tests/` and `.planning/`; the server implementation should change only if integration findings expose a real defect.
- Reuse the existing public entrypoint in [`__main__.py`](/home/berga/Workspace/projects/logseq-mcp/src/logseq_mcp/__main__.py). Do not add a second launcher path just for tests.
- Preserve the stderr-only logging contract from Phase 1. Any extra debug output to stdout will break MCP framing.
- Reuse the real tool registry from [`server.py`](/home/berga/Workspace/projects/logseq-mcp/src/logseq_mcp/server.py); Phase 4 should verify the same process Claude will run.
- Keep graph isolation explicit. Do not infer safety from page names alone.
- Assume Logseq API access still requires the desktop app to be running with the intended graph open.

---

## Recommended Test Architecture

### Test layers

1. Keep the existing unit tests in [`tests/test_core.py`](/home/berga/Workspace/projects/logseq-mcp/tests/test_core.py), [`tests/test_write.py`](/home/berga/Workspace/projects/logseq-mcp/tests/test_write.py), and [`tests/test_server.py`](/home/berga/Workspace/projects/logseq-mcp/tests/test_server.py) as fast regression coverage.
2. Add a new integration module for live Logseq API verification against an isolated graph.
3. Add a stdio-level MCP integration module that launches `python -m logseq_mcp` as a subprocess and invokes tools through MCP protocol.
4. Keep the `~/.claude/.mcp.json` swap and Claude daily-driver check as a manual gate, not an automated test.

### Suggested file split

```text
tests/
├── integration/
│   ├── conftest.py                  # graph/env guards, subprocess helpers
│   ├── test_live_graph.py           # isolated graph read/write verification
│   ├── test_mcp_stdio.py            # black-box MCP stdio launch + tool calls
│   └── test_graphthulhu_parity.py   # parity comparison on known page
└── fixtures/
    └── graph/
        ├── pages/
        │   ├── parity-page.md
        │   └── write-sandbox.md
        └── README.md
```

### Recommended execution model

- Default `pytest` run should keep unit tests only.
- Live integration tests should run behind an explicit marker such as `-m integration`.
- Parity tests should also be explicit because they depend on graphthulhu still being available.
- Each integration test should assert the active graph name before any mutation.

This keeps the normal dev loop fast while making integration intent explicit.

---

## MCP Stdio Verification

Phase 4 should prove these specific facts for INTG-01:

1. `uv run python -m logseq_mcp` starts successfully and stays alive long enough to complete MCP initialization.
2. stdout contains valid MCP traffic only; logs remain on stderr.
3. `tools/list` returns at least `health`, `get_page`, `get_block`, `list_pages`, `get_references`, `page_create`, `block_append`, `block_update`, and `block_delete`.
4. `tools/call` works for one read tool and one write tool through MCP transport, not by importing Python functions directly.
5. Environment propagation works: the launched process can reach the same Logseq API token and URL configuration as the shell that started it.

Recommended harness behavior:

- start subprocess with a minimal env override
- initialize MCP session
- call `health`
- verify reported graph name matches the isolated test graph
- call `get_page` on the parity fixture page
- create or mutate one sandbox page and confirm readback
- terminate process cleanly and assert no stdout garbage outside protocol frames

---

## Isolated Test Graph Setup

The isolated graph plan needs to be concrete because Logseq has no true headless graph server in this repo.

### Recommended setup

- Create a dedicated graph with a distinct name such as `logseq-mcp-test`.
- Store seed markdown files for required pages under repo fixtures so the graph can be recreated deterministically.
- Include one parity page that intentionally contains nested blocks where graphthulhu previously over-counted.
- Include one sandbox page or namespace reserved for destructive write tests.
- Add a preflight helper that checks `health["graph"]` and aborts if the wrong graph is open.

### Required seeded content

- `Parity Fixture` page: nested structure with at least one branch deep enough to exercise deduplication visibly.
- `Write Sandbox` page: safe target for append, update, and delete tests.
- Optional namespace page set for `list_pages` verification if Phase 4 broadens beyond `get_page`.

### Safety rules

- Never run live write tests against the daily workspace graph.
- Do not share the sandbox page name with real notes.
- If the wrong graph is active, fail before the first mutation.

---

## Graphthulhu Parity Strategy

INTG-03 should be planned as a controlled comparison, not a vague manual check.

### Comparison target

Pick one known page in the isolated graph that has:

- multiple top-level blocks
- nested children
- enough depth to reveal duplication if traversal is wrong

### Comparison assertions

- `page.name` is the same from both servers
- `logseq-mcp` returns no duplicate UUIDs anywhere in the tree
- `logseq-mcp` preserves expected child nesting
- `logseq-mcp` returns block count less than or equal to graphthulhu on the fixture page
- if counts differ, the extra graphthulhu blocks are explainable as duplicated UUIDs rather than missing content from `logseq-mcp`

### Practical strategy

- Keep graphthulhu configured and runnable until this check passes.
- Compare normalized structures extracted from each server response.
- Record the exact fixture page name in the Phase 4 plan so the result is reproducible.

The planner should explicitly reject a parity approach that only compares human-readable summaries. This requirement is about structural correctness.

---

## Risks

### Integration risks

- MCP stdio may fail despite passing import-level tests if stdout is contaminated or the subprocess dies early.
- Claude may launch the server with a different working directory or environment than the shell tests use.
- Logseq may be running the wrong graph even when the API is reachable.

### Test-environment risks

- The desktop-app dependency makes CI-style automation harder; local operator steps must be documented precisely.
- Seed graph drift can invalidate parity expectations if fixture pages are edited manually.
- Write tests can become flaky if they reuse mutated pages instead of recreating or namespacing test data.

### Product risks

- Swapping `~/.claude/.mcp.json` too early can break daily workflow even if unit and integration tests pass.
- Removing graphthulhu before collecting parity evidence makes rollback harder.

---

## Common Pitfalls

- Testing `mcp._tool_manager._tools` and assuming that proves MCP transport works.
- Comparing graphthulhu and `logseq-mcp` raw JSON without normalizing for the deduplication fix.
- Running integration writes against the real graph because the API token is valid and `health` looks healthy.
- Assuming `python -m logseq_mcp` and Claude's MCP launcher use identical env and cwd behavior.
- Treating the `~/.claude/.mcp.json` edit as reversible trivia rather than a deployment change that needs a rollback path.

---

## Don't Hand-Roll

- Do not hand-roll JSON-RPC framing if the installed `mcp` package already provides usable client/session helpers.
- Do not build a custom graph diff engine; a small recursive normalizer for page/block structure is enough.
- Do not create a fake in-memory Logseq server for INTG-02 or INTG-03. This phase needs the real Logseq HTTP API.
- Do not invent a second entrypoint for tests; validate the shipped module path directly.

---

## Manual Verification for `~/.claude/.mcp.json`

The Phase 4 plan should reserve a manual verification block after automated tests pass.

### Recommended sequence

1. Back up the current `~/.claude/.mcp.json`.
2. Confirm graphthulhu is still available as the rollback option.
3. Add or replace the server entry so Claude launches `uv run python -m logseq_mcp` in this repo with the required env.
4. Restart or reload Claude MCP connections.
5. Run a short daily-driver script through Claude:
   - `health`
   - `get_page` on a known working note
   - one non-destructive read like `list_pages`
   - one safe write on the isolated graph or sandbox page if the workflow allows it
6. Confirm no regression in normal Claude usage.
7. Only then remove graphthulhu from the config if desired.

### Manual acceptance criteria

- Claude can discover the server and list tools.
- Claude can call at least one read tool and one write tool successfully.
- No MCP protocol errors appear after reload.
- Rollback instructions are documented if the new config fails.

---

## Validation Architecture

The orchestrator should generate `VALIDATION.md` around four validation layers for Phase 4.

### 1. Environment validation

- required env vars are present
- Logseq desktop app is running
- active graph name matches the isolated test graph
- graphthulhu availability is confirmed before parity tests start

### 2. Transport validation

- `uv run python -m logseq_mcp` launches successfully
- MCP initialization completes over stdio
- stdout carries protocol traffic only
- expected tools are discoverable through `tools/list`

### 3. State validation

- live read and write operations succeed against the isolated graph
- read-after-write checks confirm page/block state in Logseq, not just RPC return values
- mutations are scoped to sandbox fixture pages only

### 4. Migration validation

- graphthulhu parity is recorded on the selected fixture page
- `~/.claude/.mcp.json` is updated deliberately and backed up first
- Claude daily-driver usage succeeds after the swap
- rollback path is documented and tested at least once manually

### Recommended validation split

- Wave 1: isolated-graph fixtures and environment guards
- Wave 2: stdio subprocess verification and MCP tool invocation
- Wave 3: graphthulhu parity comparison and manual config swap verification

### Nyquist-critical checks

- No Phase 4 plan should go three tasks without a concrete verification command or manual checkpoint.
- INTG-01 must be validated through MCP stdio, not only Python imports.
- INTG-02 must fail closed when the wrong graph is open.
- INTG-03 must prove that any block-count difference is due to deduplication, not missing data.

---

## Planning Recommendations

- Plan Phase 4 as three plans, one per success criterion: stdio launch, isolated integration graph, parity plus swap.
- Put the isolated-graph preflight guard in the first Phase 4 plan so later work cannot accidentally hit the wrong graph.
- Keep graphthulhu in place until the parity fixture comparison and Claude config verification both pass.
- Require a documented manual checkpoint for the `~/.claude/.mcp.json` edit; this is the production cutover.
- Treat any Phase 4 server code changes as bug-fix fallout from integration evidence, not as the primary deliverable.
