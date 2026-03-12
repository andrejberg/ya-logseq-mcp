---
phase: 4
slug: integration-and-swap
status: complete
nyquist_compliant: true
wave_1_complete: true
created: 2026-03-10
audited: 2026-03-12
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + pytest-asyncio |
| **Config file** | `pyproject.toml` — `[tool.pytest.ini_options]` sets `asyncio_mode = "auto"` |
| **Quick run command** | `source ~/Workspace/.env && uv run pytest tests/integration/test_live_graph.py -x -q -m integration`; `source ~/Workspace/.env && uv run pytest tests/integration/test_mcp_stdio.py -x -q -m integration`; `source ~/Workspace/.env && uv run pytest tests/integration/test_graphthulhu_parity.py -x -q -m integration` |
| **Full suite command** | `uv run pytest tests/ -q -m "not integration"` followed by `source ~/Workspace/.env && uv run pytest tests/integration -q -m integration` |
| **Estimated runtime** | ~1 second for live graph, ~3 seconds for stdio, ~2 seconds for parity, ~5 seconds for the combined validation slice |

---

## Sampling Rate

- **After every task commit:** Run the wave-specific integration slice for the changed area
- **After every plan wave:** Run the affected integration slice plus `uv run pytest tests/ -q -m "not integration"`
- **Before `$gsd-verify-work`:** Both the non-integration suite and the integration suite must be green with the isolated test graph active
- **Max feedback latency:** ~5 seconds for the full validation loop

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 4-01-01 | 01 | 1 | INTG-02 | fixture + env guard | `source ~/Workspace/.env && uv run pytest tests/integration/test_live_graph.py::test_health_requires_isolated_graph -q -m integration` | ✅ `tests/integration/test_live_graph.py` | ✅ green |
| 4-01-02 | 01 | 1 | INTG-02 | live read/write | `source ~/Workspace/.env && uv run pytest tests/integration/test_live_graph.py::test_write_tools_use_sandbox_page_only -q -m integration` | ✅ `tests/integration/test_live_graph.py` | ✅ green |
| 4-01-03 | 01 | 1 | INTG-02 | fixture docs + flow | `source ~/Workspace/.env && uv run pytest tests/integration/test_live_graph.py -q -m integration` | ✅ `tests/integration/test_live_graph.py` | ✅ green |
| 4-02-01 | 02 | 2 | INTG-01 | stdio transport | `source ~/Workspace/.env && uv run pytest tests/integration/test_mcp_stdio.py::test_stdio_server_exposes_expected_tools -q -m integration` | ✅ `tests/integration/test_mcp_stdio.py` | ✅ green |
| 4-02-02 | 02 | 2 | INTG-01 | MCP tool call | `source ~/Workspace/.env && uv run pytest tests/integration/test_mcp_stdio.py::test_mcp_health_and_get_page_round_trip -q -m integration` | ✅ `tests/integration/test_mcp_stdio.py` | ✅ green |
| 4-02-03 | 02 | 2 | INTG-01 | stdout/stderr hygiene | `source ~/Workspace/.env && uv run pytest tests/integration/test_mcp_stdio.py::test_server_keeps_logs_off_stdout -q -m integration` | ✅ `tests/integration/test_mcp_stdio.py` | ✅ green |
| 4-02-04 | 02 | 2 | INTG-01, INTG-02 | MCP write round trip | `source ~/Workspace/.env && uv run pytest tests/integration/test_mcp_stdio.py::test_mcp_write_round_trip_uses_isolated_graph -q -m integration` | ✅ `tests/integration/test_mcp_stdio.py` | ✅ green |
| 4-03-01 | 03 | 3 | INTG-03 | parity structural diff | `source ~/Workspace/.env && uv run pytest tests/integration/test_graphthulhu_parity.py::test_get_page_parity_fixture_has_fewer_duplicate_blocks_than_graphthulhu -q -m integration` | ✅ `tests/integration/test_graphthulhu_parity.py` | ✅ green |
| 4-03-02 | 03 | 3 | INTG-01..03 | integration sweep | `source ~/Workspace/.env && uv run pytest tests/integration -q -m integration` | ✅ `tests/integration/` | ✅ green |
| 4-03-03 | 03 | 3 | INTG-01 | migration baseline | `uv run pytest tests/ -q -m "not integration"` | ✅ `tests/` | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 1 Requirements

- [x] `tests/integration/conftest.py` — isolated graph guards, env fixtures, and deterministic sandbox reset helpers
- [x] `tests/integration/test_live_graph.py` — health preflight plus sandboxed live read/write checks
- [x] `tests/fixtures/graph/pages/parity-page.md` — deterministic nested fixture page
- [x] `tests/fixtures/graph/pages/write-sandbox.md` — safe mutation target
- [x] `tests/fixtures/graph/README.md` — operator setup for opening the isolated Logseq graph

## Later-Wave Requirements

- [x] Wave 2: `tests/integration/test_mcp_stdio.py` — black-box MCP stdio launch and tool invocation
- [x] Wave 3: `tests/integration/test_graphthulhu_parity.py` — parity fixture comparison against graphthulhu

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Update `~/.claude/.mcp.json` with rollback protection and reload Claude MCP connections | INTG-01 | The production Claude config lives outside the repo and should be changed deliberately after automated validation passes | Back up `~/.claude/.mcp.json`, add or replace the `logseq-mcp` server entry, reload Claude MCP connections, verify tool discovery, then restore the backup if any call fails |
| Daily-driver smoke check after swap | INTG-01, INTG-03 | Claude workflow continuity cannot be proven fully from pytest alone | First validate the isolated graph flow with `health`, `get_page` on the parity page, `list_pages`, and one safe sandbox write. Then switch back to the real daily-driver graph and run a read-only Claude smoke test against a known note or namespace before declaring the swap safe |
| Final graphthulhu removal decision | INTG-03 | Rollback readiness is an operational decision, not just a test assertion | Keep graphthulhu configured until parity evidence and Claude smoke checks both pass, then remove it only after confirming rollback steps still work |

---

## Coverage Audit

| Requirement | Coverage | Evidence |
|-------------|----------|----------|
| INTG-01 | COVERED | `tests/integration/test_mcp_stdio.py` verifies production stdio startup, tool discovery, read round trips, write round trips, and stdout/stderr hygiene |
| INTG-02 | COVERED | `tests/integration/test_live_graph.py` verifies isolated graph enforcement, fixture presence, and sandbox-only destructive flows |
| INTG-03 | COVERED | `tests/integration/test_graphthulhu_parity.py` verifies structural parity and the deduplication win against graphthulhu on the parity fixture |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or an explicit manual checkpoint
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 1 covers all missing integration artifacts and fixture docs
- [x] No watch-mode flags
- [x] Feedback latency < 45s for the quick loop once integration files exist
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** complete

---

## Validation Audit 2026-03-12

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |

Audit result:

- Existing Phase 4 validation coverage was complete once the active Logseq graph was switched back to `logseq-test-graph`.
- `source ~/Workspace/.env && uv run pytest tests/integration/test_live_graph.py -x -q -m integration` passed with `3 passed`.
- `source ~/Workspace/.env && uv run pytest tests/integration/test_mcp_stdio.py -x -q -m integration` passed with `4 passed`.
- `source ~/Workspace/.env && uv run pytest tests/integration/test_graphthulhu_parity.py -x -q -m integration` passed with `2 passed`.
- `uv run pytest tests/ -q -m "not integration"` passed with `38 passed, 9 deselected`.
