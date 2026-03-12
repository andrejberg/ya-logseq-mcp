---
phase: 7
slug: journal-range-and-milestone-validation
status: draft
nyquist_compliant: false
wave_1_complete: false
created: 2026-03-12
---

# Phase 7 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + pytest-asyncio |
| **Config file** | `pyproject.toml` — `[tool.pytest.ini_options]` sets asyncio/integration markers |
| **Quick run command** | `uv run pytest tests/test_write.py -x -q`; `uv run pytest tests/test_server.py -q`; `source ~/Workspace/.env && uv run pytest tests/integration/test_mcp_stdio.py -x -q -m integration`; `source ~/Workspace/.env && uv run pytest tests/integration/test_live_graph.py -x -q -m integration` |
| **Full suite command** | `uv run pytest tests/ -q -m "not integration"` followed by `source ~/Workspace/.env && uv run pytest tests/integration -q -m integration` |
| **Estimated runtime** | ~10-15 seconds for focused slices, ~25-30 seconds for full phase loop |

---

## Sampling Rate

- **After every task commit:** Run the smallest phase-relevant test slice for changed area
- **After every plan wave:** Run non-integration suite + affected integration slice on isolated graph
- **Before `$gsd-verify-work`:** Full non-integration and integration suites must be green
- **Max feedback latency:** ~30 seconds for full validation loop

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 7-01-01 | 01 | 1 | JOUR-03 | unit range contract | `uv run pytest tests/test_write.py -x -q` | ✅ `tests/test_write.py` | ⬜ pending |
| 7-01-02 | 01 | 1 | JOUR-03 | unit explicit failure modes | `uv run pytest tests/test_write.py -x -q` | ✅ `tests/test_write.py` | ⬜ pending |
| 7-01-03 | 01 | 1 | JOUR-03 | unit ordering and bounded lookup guard | `uv run pytest tests/test_write.py -x -q` | ✅ `tests/test_write.py` | ⬜ pending |
| 7-02-01 | 02 | 2 | JOUR-03 | registry exposure | `uv run pytest tests/test_server.py -q` | ✅ `tests/test_server.py` | ⬜ pending |
| 7-02-02 | 02 | 2 | JOUR-03 | stdio transport flow | `source ~/Workspace/.env && uv run pytest tests/integration/test_mcp_stdio.py -x -q -m integration` | ✅ `tests/integration/test_mcp_stdio.py` | ⬜ pending |
| 7-03-01 | 03 | 3 | JOUR-03 | live isolated range behavior | `source ~/Workspace/.env && uv run pytest tests/integration/test_live_graph.py -x -q -m integration` | ✅ `tests/integration/test_live_graph.py` | ⬜ pending |
| 7-03-02 | 03 | 3 | JOUR-03 | live destructive + journal milestone regression | `source ~/Workspace/.env && uv run pytest tests/integration/test_live_graph.py -x -q -m integration` | ✅ `tests/integration/test_live_graph.py` | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 1 Requirements

- [ ] `tests/test_write.py` — `journal_range` inclusive range, invalid/reversed date errors, bounded span, and entry ordering
- [ ] `tests/test_server.py` — expected tool registry includes `journal_range`
- [ ] `tests/integration/test_mcp_stdio.py` — stdio list-tools + call-flow checks for `journal_range`
- [ ] `tests/integration/test_live_graph.py` — isolated graph assertions for inclusive existing entries and reversed-range failure

*Existing pytest and isolated-graph infrastructure from prior phases should be reused.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Milestone narrative and requirement traceability are updated consistently across planning docs | JOUR-03 | Automated tests prove runtime behavior but not doc-level milestone sign-off quality | Review `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`, and phase verification artifacts after green automation; confirm JOUR-03 closure evidence is explicit and consistent |

---

## Coverage Audit

| Requirement | Coverage Goal | Evidence Expected |
|-------------|---------------|------------------|
| JOUR-03 | Inclusive journal range reads with explicit invalid/reversed failures and bounded lookup; stdio/live validation for v1.1 surface | `tests/test_write.py`, `tests/test_server.py`, `tests/integration/test_mcp_stdio.py`, `tests/integration/test_live_graph.py` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or an explicit manual checkpoint
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 1 covers fixture and helper scaffolding before public tool + milestone gate checks
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s for quick validation loop
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
