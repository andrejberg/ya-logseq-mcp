---
phase: 6
slug: block-moves-and-journal-writes
status: draft
nyquist_compliant: false
wave_1_complete: false
created: 2026-03-12
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + pytest-asyncio |
| **Config file** | `pyproject.toml` — `[tool.pytest.ini_options]` sets `asyncio_mode = "auto"` and integration markers |
| **Quick run command** | `uv run pytest tests/test_write.py -x -q`; `uv run pytest tests/test_server.py -q`; `source ~/Workspace/.env && uv run pytest tests/integration/test_live_graph.py -x -q -m integration`; `source ~/Workspace/.env && uv run pytest tests/integration/test_mcp_stdio.py -x -q -m integration` |
| **Full suite command** | `uv run pytest tests/ -q -m "not integration"` followed by `source ~/Workspace/.env && uv run pytest tests/integration -q -m integration` |
| **Estimated runtime** | ~10 seconds for unit and registry checks, ~15 seconds for live move and journal slices, ~25 seconds for the full validation loop |

---

## Sampling Rate

- **After every task commit:** Run the smallest phase-relevant slice for the changed area
- **After every plan wave:** Run `uv run pytest tests/ -q -m "not integration"` plus the affected integration slice with `source ~/Workspace/.env`
- **Before `$gsd-verify-work`:** Both the non-integration suite and integration suite must be green with the isolated graph active
- **Max feedback latency:** ~25 seconds for the full validation loop

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 6-01-01 | 01 | 1 | WRIT-08 | unit scaffold | `uv run pytest tests/test_write.py -x -q` | ✅ `tests/test_write.py` | ⬜ pending |
| 6-01-02 | 01 | 1 | WRIT-08 | integration move fixture | `source ~/Workspace/.env && uv run pytest tests/integration/test_live_graph.py -x -q -m integration` | ✅ `tests/integration/test_live_graph.py` | ⬜ pending |
| 6-01-03 | 01 | 1 | WRIT-08 | stdio move coverage | `source ~/Workspace/.env && uv run pytest tests/integration/test_mcp_stdio.py -x -q -m integration` | ✅ `tests/integration/test_mcp_stdio.py` | ⬜ pending |
| 6-02-01 | 02 | 2 | JOUR-01 | unit date-resolution and create-if-missing | `uv run pytest tests/test_write.py -x -q` | ✅ `tests/test_write.py` | ⬜ pending |
| 6-02-02 | 02 | 2 | JOUR-01 | live journal resolution | `source ~/Workspace/.env && uv run pytest tests/integration/test_live_graph.py -x -q -m integration` | ✅ `tests/integration/test_live_graph.py` | ⬜ pending |
| 6-02-03 | 02 | 2 | JOUR-01 | server registration | `uv run pytest tests/test_server.py -q` | ✅ `tests/test_server.py` | ⬜ pending |
| 6-03-01 | 03 | 2 | JOUR-02 | unit nested append reuse | `uv run pytest tests/test_write.py -x -q` | ✅ `tests/test_write.py` | ⬜ pending |
| 6-03-02 | 03 | 2 | JOUR-02 | live nested journal append | `source ~/Workspace/.env && uv run pytest tests/integration/test_live_graph.py -x -q -m integration` | ✅ `tests/integration/test_live_graph.py` | ⬜ pending |
| 6-03-03 | 03 | 2 | JOUR-02 | MCP stdio journal coverage | `source ~/Workspace/.env && uv run pytest tests/integration/test_mcp_stdio.py -x -q -m integration` | ✅ `tests/integration/test_mcp_stdio.py` | ⬜ pending |
| 6-05-01 | 05 | 2 | WRIT-08 | unit cross-page move verification | `uv run pytest tests/test_write.py -x -q` | ✅ `tests/test_write.py` | ⬜ pending |
| 6-05-02 | 05 | 2 | WRIT-08 | live cross-page move verification | `source ~/Workspace/.env && uv run pytest tests/integration/test_live_graph.py -x -q -m integration` | ✅ `tests/integration/test_live_graph.py` | ⬜ pending |
| 6-05-03 | 05 | 2 | WRIT-08 | MCP stdio cross-page move verification | `source ~/Workspace/.env && uv run pytest tests/integration/test_mcp_stdio.py -x -q -m integration` | ✅ `tests/integration/test_mcp_stdio.py` | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 1 Requirements

- [ ] `tests/test_write.py` — red-state move and journal tests covering valid positions, invalid positions, malformed dates, and create-if-missing behavior
- [ ] `tests/integration/conftest.py` — disposable move-tree and journal-date helpers for the isolated graph
- [ ] `tests/integration/test_live_graph.py` — explicit move semantics and journal create/append coverage against disposable fixtures
- [ ] `tests/integration/test_mcp_stdio.py` — expected-tool-list and call-flow coverage for `move_block`, `journal_today`, and `journal_append`

*Existing pytest and isolated-graph infrastructure from earlier phases should be reused rather than replaced.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Moved block order matches UI expectations after repeated before/after/child operations | WRIT-08 | Automated tests can prove tree structure via API readback, but not whether the editor UI presents the reordered subtree exactly as a user expects | In the isolated graph, run each move mode through the MCP tool path, then inspect the page in Logseq to confirm subtree placement and indentation match the requested relationship |

---

## Coverage Audit

| Requirement | Coverage Goal | Evidence Expected |
|-------------|---------------|------------------|
| WRIT-08 | Move proves requested relationship and subtree preservation in unit, live, and MCP stdio paths, including a cross-page target scenario | `tests/test_write.py`, `tests/integration/test_live_graph.py`, `tests/integration/test_mcp_stdio.py` |
| JOUR-01 | Journal today resolves or creates the expected page and returns stable readback on graphs using Logseq `yyyy-MM-dd` journal page titles | `tests/test_write.py`, `tests/integration/test_live_graph.py`, `tests/test_server.py` |
| JOUR-02 | Journal append reuses nested append guarantees and proves resulting tree shape on graphs using Logseq `yyyy-MM-dd` journal page titles | `tests/test_write.py`, `tests/integration/test_live_graph.py`, `tests/integration/test_mcp_stdio.py` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or an explicit manual checkpoint
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 1 covers fixture and helper scaffolding before public tool delivery
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s for the quick validation loop
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
