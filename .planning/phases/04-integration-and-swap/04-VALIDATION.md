---
phase: 4
slug: integration-and-swap
status: draft
nyquist_compliant: false
wave_1_complete: false
created: 2026-03-10
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + pytest-asyncio |
| **Config file** | `pyproject.toml` — `[tool.pytest.ini_options]` sets `asyncio_mode = "auto"` |
| **Quick run command** | Wave 1: `uv run pytest tests/integration/test_live_graph.py -x -q -m integration`; Wave 2: `uv run pytest tests/integration/test_mcp_stdio.py -x -q -m integration`; Wave 3: `uv run pytest tests/integration/test_graphthulhu_parity.py -x -q -m integration` |
| **Full suite command** | `uv run pytest tests/ -v -m "not integration"` followed by `uv run pytest tests/integration -v -m integration` |
| **Estimated runtime** | ~20 seconds for quick checks, ~45 seconds for full suite with live graph open |

---

## Sampling Rate

- **After every task commit:** Run the wave-specific quick command for the current plan:
  Wave 1 `uv run pytest tests/integration/test_live_graph.py -x -q -m integration`; Wave 2 `uv run pytest tests/integration/test_mcp_stdio.py -x -q -m integration`; Wave 3 `uv run pytest tests/integration/test_graphthulhu_parity.py -x -q -m integration`
- **After every plan wave:** Run the relevant integration slice for that wave, then `uv run pytest tests/ -v -m "not integration"`
- **Before `$gsd-verify-work`:** Both suites must be green with the isolated test graph open: `uv run pytest tests/ -v -m "not integration"` and `uv run pytest tests/integration -v -m integration`
- **Max feedback latency:** ~45 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 4-01-01 | 01 | 1 | INTG-02 | fixture + env guard | `uv run pytest tests/integration/test_live_graph.py::test_health_requires_isolated_graph -x -q -m integration` | ❌ Wave 1 | ⬜ pending |
| 4-01-02 | 01 | 1 | INTG-02 | live read/write | `uv run pytest tests/integration/test_live_graph.py::test_write_tools_use_sandbox_page_only -x -q -m integration` | ❌ Wave 1 | ⬜ pending |
| 4-01-03 | 01 | 1 | INTG-02 | fixture docs | `uv run pytest tests/integration/test_live_graph.py -x -q -m integration` | ❌ Wave 1 | ⬜ pending |
| 4-02-01 | 02 | 2 | INTG-01 | stdio transport | `uv run pytest tests/integration/test_mcp_stdio.py::test_stdio_server_exposes_expected_tools -x -q -m integration` | ❌ Wave 1 | ⬜ pending |
| 4-02-02 | 02 | 2 | INTG-01 | MCP tool call | `uv run pytest tests/integration/test_mcp_stdio.py::test_mcp_health_and_get_page_round_trip -x -q -m integration` | ❌ Wave 1 | ⬜ pending |
| 4-02-03 | 02 | 2 | INTG-01 | stdout/stderr hygiene | `uv run pytest tests/integration/test_mcp_stdio.py::test_server_keeps_logs_off_stdout -x -q -m integration` | ❌ Wave 1 | ⬜ pending |
| 4-03-01 | 03 | 3 | INTG-03 | parity structural diff | `uv run pytest tests/integration/test_graphthulhu_parity.py::test_get_page_parity_fixture_has_fewer_duplicate_blocks_than_graphthulhu -x -q -m integration` | ❌ Wave 1 | ⬜ pending |
| 4-03-02 | 03 | 3 | INTG-01..03 | integration sweep | `uv run pytest tests/integration -v -m integration` | ❌ Wave 1 | ⬜ pending |
| 4-03-03 | 03 | 3 | INTG-01 | manual migration gate | `uv run pytest tests/ -v -m "not integration"` | ✅ existing | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 1 Requirements

- [ ] `tests/integration/conftest.py` — isolated graph guards, env fixtures, and deterministic sandbox reset helpers
- [ ] `tests/integration/test_live_graph.py` — health preflight plus sandboxed live read/write checks
- [ ] `tests/fixtures/graph/pages/parity-page.md` — deterministic nested fixture page
- [ ] `tests/fixtures/graph/pages/write-sandbox.md` — safe mutation target
- [ ] `tests/fixtures/graph/README.md` — operator setup for opening the isolated Logseq graph

## Later-Wave Requirements

- [ ] Wave 2: `tests/integration/test_mcp_stdio.py` — black-box MCP stdio launch and tool invocation
- [ ] Wave 3: `tests/integration/test_graphthulhu_parity.py` — parity fixture comparison against graphthulhu

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Update `~/.claude/.mcp.json` with rollback protection and reload Claude MCP connections | INTG-01 | The production Claude config lives outside the repo and should be changed deliberately after automated validation passes | Back up `~/.claude/.mcp.json`, add or replace the `logseq-mcp` server entry, reload Claude MCP connections, verify tool discovery, then restore the backup if any call fails |
| Daily-driver smoke check after swap | INTG-01, INTG-03 | Claude workflow continuity cannot be proven fully from pytest alone | First validate the isolated graph flow with `health`, `get_page` on the parity page, `list_pages`, and one safe sandbox write. Then switch back to the real daily-driver graph and run a read-only Claude smoke test against a known note or namespace before declaring the swap safe |
| Final graphthulhu removal decision | INTG-03 | Rollback readiness is an operational decision, not just a test assertion | Keep graphthulhu configured until parity evidence and Claude smoke checks both pass, then remove it only after confirming rollback steps still work |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or an explicit manual checkpoint
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 1 covers all missing integration artifacts and fixture docs
- [ ] No watch-mode flags
- [ ] Feedback latency < 45s for the quick loop once integration files exist
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
