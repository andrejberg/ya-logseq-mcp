---
phase: 2
slug: core-reads
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-03-09
audited: 2026-03-12
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 + pytest-asyncio 1.3.0 |
| **Config file** | `pyproject.toml` — `[tool.pytest.ini_options]` asyncio_mode = "auto" |
| **Quick run command** | `uv run pytest tests/test_core.py -q` |
| **Full suite command** | `uv run pytest tests/ -q -m "not integration"` |
| **Estimated runtime** | ~1 second for `tests/test_core.py`, ~1 second for the non-integration suite |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/test_core.py -q`
- **After every plan wave:** Run `uv run pytest tests/ -q -m "not integration"`
- **Before `/gsd:verify-work`:** Phase read-surface tests and the broader non-integration suite must be green
- **Max feedback latency:** ~1 second

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 2-01-01 | 01 | 0 | READ-01..06 | unit scaffold | `uv run pytest tests/test_core.py -q` | ✅ `tests/test_core.py` | ✅ green |
| 2-01-02 | 01 | 1 | READ-01 | unit | `uv run pytest tests/test_core.py::test_get_page_no_duplicate_uuids -q` | ✅ `tests/test_core.py` | ✅ green |
| 2-01-03 | 01 | 1 | READ-02 | unit | `uv run pytest tests/test_core.py::test_get_page_nesting_correct -q` | ✅ `tests/test_core.py` | ✅ green |
| 2-01-04 | 01 | 1 | READ-03 | unit | `uv run pytest tests/test_core.py::test_get_page_uses_name -q` | ✅ `tests/test_core.py` | ✅ green |
| 2-02-01 | 02 | 1 | READ-04 | unit | `uv run pytest tests/test_core.py::test_get_block_returns_block -q` | ✅ `tests/test_core.py` | ✅ green |
| 2-02-02 | 02 | 1 | READ-05 | unit | `uv run pytest tests/test_core.py::test_list_pages_namespace_filter -q` | ✅ `tests/test_core.py` | ✅ green |
| 2-02-03 | 02 | 1 | READ-06 | unit | `uv run pytest tests/test_core.py::test_get_references_parses_response -q` | ✅ `tests/test_core.py` | ✅ green |
| 2-02-04 | 02 | 1 | READ-05 regression | unit | `uv run pytest tests/test_core.py::test_list_pages_tolerates_namespace_page_refs -q` | ✅ `tests/test_core.py` | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/test_core.py` — stubs for READ-01 through READ-06

*All existing test files (`test_client.py`, `test_types.py`, `test_server.py`) remain valid — no changes needed.*

*Framework already installed from Phase 1: pytest 9.0.2 + pytest-asyncio 1.3.0, asyncio_mode = "auto".*

---

## Manual-Only Verifications

*All phase behaviors have automated verification.*

---

## Coverage Audit

| Requirement | Coverage | Evidence |
|-------------|----------|----------|
| READ-01 | COVERED | `test_get_page_no_duplicate_uuids` verifies UUID deduplication when the same block appears both nested and at top level |
| READ-02 | COVERED | `test_get_page_nesting_correct` verifies the duplicate child remains nested under its parent and is removed from top level |
| READ-03 | COVERED | `test_get_page_uses_name` verifies `getPageBlocksTree` is called with the page name string |
| READ-04 | COVERED | `test_get_block_returns_block` verifies single-block lookup output |
| READ-05 | COVERED | `test_list_pages_namespace_filter` plus `test_list_pages_tolerates_namespace_page_refs` verify namespace filtering and production payload tolerance |
| READ-06 | COVERED | `test_get_references_parses_response` verifies linked-reference normalization |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 5s
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

- Existing Phase 2 validation coverage was complete; no new tests were needed.
- `uv run pytest tests/test_core.py -q` passed with `7 passed`.
- `uv run pytest tests/ -q -m "not integration"` passed with `38 passed, 9 deselected`.
