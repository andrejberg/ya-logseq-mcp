---
phase: 2
slug: core-reads
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-09
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 + pytest-asyncio 1.3.0 |
| **Config file** | `pyproject.toml` — `[tool.pytest.ini_options]` asyncio_mode = "auto" (already set) |
| **Quick run command** | `uv run pytest tests/ -x -q` |
| **Full suite command** | `uv run pytest tests/ -v` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/ -x -q`
- **After every plan wave:** Run `uv run pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** ~5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 2-01-01 | 01 | 0 | READ-01..06 | unit stubs | `uv run pytest tests/test_core.py -x -q` | ❌ Wave 0 | ⬜ pending |
| 2-01-02 | 01 | 1 | READ-01 | unit | `uv run pytest tests/test_core.py::test_get_page_no_duplicate_uuids -x` | ❌ Wave 0 | ⬜ pending |
| 2-01-03 | 01 | 1 | READ-02 | unit | `uv run pytest tests/test_core.py::test_get_page_nesting_correct -x` | ❌ Wave 0 | ⬜ pending |
| 2-01-04 | 01 | 1 | READ-03 | unit | `uv run pytest tests/test_core.py::test_get_page_uses_name -x` | ❌ Wave 0 | ⬜ pending |
| 2-02-01 | 02 | 1 | READ-04 | unit | `uv run pytest tests/test_core.py::test_get_block_returns_block -x` | ❌ Wave 0 | ⬜ pending |
| 2-02-02 | 02 | 1 | READ-05 | unit | `uv run pytest tests/test_core.py::test_list_pages_namespace_filter -x` | ❌ Wave 0 | ⬜ pending |
| 2-02-03 | 02 | 1 | READ-06 | unit | `uv run pytest tests/test_core.py::test_get_references_parses_response -x` | ❌ Wave 0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_core.py` — stubs for READ-01 through READ-06 (new file)

*All existing test files (`test_client.py`, `test_types.py`, `test_server.py`) remain valid — no changes needed.*

*Framework already installed from Phase 1: pytest 9.0.2 + pytest-asyncio 1.3.0, asyncio_mode = "auto".*

---

## Manual-Only Verifications

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
