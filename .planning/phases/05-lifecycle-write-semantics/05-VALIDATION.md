---
phase: 5
slug: lifecycle-write-semantics
status: draft
nyquist_compliant: false
wave_1_complete: false
created: 2026-03-12
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + pytest-asyncio |
| **Config file** | `pyproject.toml` — `[tool.pytest.ini_options]` sets `asyncio_mode = "auto"` and integration markers |
| **Quick run command** | `uv run pytest tests/test_write.py -x -q`; `uv run pytest tests/test_server.py -q`; `source ~/Workspace/.env && uv run pytest tests/integration/test_live_graph.py -x -q -m integration`; `source ~/Workspace/.env && uv run pytest tests/integration/test_mcp_stdio.py -x -q -m integration` |
| **Full suite command** | `uv run pytest tests/ -q -m "not integration"` followed by `source ~/Workspace/.env && uv run pytest tests/integration -q -m integration` |
| **Estimated runtime** | ~10 seconds for unit and registry checks, ~10 seconds for the lifecycle integration slice, ~20 seconds for the combined validation loop |

---

## Sampling Rate

- **After every task commit:** Run the smallest lifecycle-relevant slice for the changed area
- **After every plan wave:** Run `uv run pytest tests/ -q -m "not integration"` plus the affected integration slice with `source ~/Workspace/.env`
- **Before `$gsd-verify-work`:** Both the non-integration suite and the integration suite must be green with the isolated graph active
- **Max feedback latency:** ~20 seconds for the full validation loop

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 5-01-01 | 01 | 1 | WRIT-06, WRIT-07 | unit scaffold | `uv run pytest tests/test_write.py -x -q` | ✅ `tests/test_write.py` | ⬜ pending |
| 5-01-02 | 01 | 1 | WRIT-06, WRIT-07 | integration helper scaffold | `source ~/Workspace/.env && uv run pytest tests/integration/test_live_graph.py -x -q -m integration` | ✅ `tests/integration/test_live_graph.py` | ⬜ pending |
| 5-01-03 | 01 | 1 | WRIT-06, WRIT-07 | stdio registry/update | `source ~/Workspace/.env && uv run pytest tests/integration/test_mcp_stdio.py -x -q -m integration` | ✅ `tests/integration/test_mcp_stdio.py` | ⬜ pending |
| 5-02-01 | 02 | 2 | WRIT-06 | unit + absence readback | `uv run pytest tests/test_write.py::test_delete_page_removes_page_from_followup_reads -x -q` | ❌ Wave 2 | ⬜ pending |
| 5-02-02 | 02 | 2 | WRIT-06 | unit negative path | `uv run pytest tests/test_write.py::test_delete_page_missing_page_raises_explicit_error -x -q` | ❌ Wave 2 | ⬜ pending |
| 5-02-03 | 02 | 2 | WRIT-07 | unit + dual readback | `uv run pytest tests/test_write.py::test_rename_page_moves_resolution_to_new_name -x -q` | ❌ Wave 2 | ⬜ pending |
| 5-02-04 | 02 | 2 | WRIT-07 | unit collision path | `uv run pytest tests/test_write.py::test_rename_page_existing_destination_raises_explicit_error -x -q` | ❌ Wave 2 | ⬜ pending |
| 5-02-05 | 02 | 2 | WRIT-06, WRIT-07 | server registration | `uv run pytest tests/test_server.py -q` | ✅ `tests/test_server.py` | ⬜ pending |
| 5-02-06 | 02 | 2 | WRIT-06, WRIT-07 | live lifecycle semantics | `source ~/Workspace/.env && uv run pytest tests/integration/test_live_graph.py -x -q -m integration` | ✅ `tests/integration/test_live_graph.py` | ⬜ pending |
| 5-02-07 | 02 | 2 | WRIT-06, WRIT-07 | MCP stdio lifecycle coverage | `source ~/Workspace/.env && uv run pytest tests/integration/test_mcp_stdio.py -x -q -m integration` | ✅ `tests/integration/test_mcp_stdio.py` | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 1 Requirements

- [ ] `tests/test_write.py` — lifecycle red-state tests for delete, rename, missing-page, and collision semantics
- [ ] `tests/integration/conftest.py` — disposable lifecycle-page helpers for create/rename/delete cleanup on the isolated graph
- [ ] `tests/integration/test_live_graph.py` — explicit lifecycle integration coverage using disposable pages instead of the fixed Phase 4 sandbox
- [ ] `tests/integration/test_mcp_stdio.py` — expected-tool-list and call-flow coverage for lifecycle tools

*Existing pytest and isolated-graph infrastructure from earlier phases should be reused rather than replaced.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Namespaced page rename matches Logseq UI expectations | WRIT-07 | Automated tests can verify API readback, but not editor presentation of namespace breadcrumbs or sidebar placement | In the isolated graph, create a disposable namespaced page, rename it through the MCP tool path, then inspect Logseq UI to confirm the new namespace path renders as expected and the old path no longer appears |
| Disposable lifecycle pages leave the isolated graph in a clean state after repeated runs | WRIT-06, WRIT-07 | Automated tests can assert target absence, but not operator confidence that fixture pages remain untouched across sessions | Run the live lifecycle slice twice in a row, then inspect the isolated graph to confirm only disposable Phase 5 pages changed and the Phase 4 fixture pages still exist unchanged |

---

## Coverage Audit

| Requirement | Coverage Goal | Evidence Expected |
|-------------|---------------|------------------|
| WRIT-06 | Delete proves absence through follow-up reads in unit, live, and MCP stdio paths | `tests/test_write.py`, `tests/integration/test_live_graph.py`, `tests/integration/test_mcp_stdio.py` |
| WRIT-07 | Rename proves new-name resolution, old-name absence, collision failure, and namespaced behavior | `tests/test_write.py`, `tests/integration/test_live_graph.py`, `tests/integration/test_mcp_stdio.py` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or an explicit manual checkpoint
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 1 covers lifecycle scaffolding and disposable-page helpers before destructive tool delivery
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s for the quick validation loop
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
