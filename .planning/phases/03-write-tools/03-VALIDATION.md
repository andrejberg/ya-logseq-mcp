---
phase: 3
slug: write-tools
status: draft
nyquist_compliant: false
wave_1_complete: false
created: 2026-03-09
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest + pytest-asyncio |
| **Config file** | `pyproject.toml` — `[tool.pytest.ini_options]` sets `asyncio_mode = "auto"` |
| **Quick run command** | `uv run pytest tests/test_write.py -x -q` |
| **Full suite command** | `uv run pytest tests/ -v` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/test_write.py -x -q`
- **After every plan wave:** Run `uv run pytest tests/ -v`
- **Before `$gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** ~10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 3-01-01 | 01 | 1 | WRIT-01..05 | unit stubs | `uv run pytest tests/test_write.py -x -q` | ❌ Wave 1 | ⬜ pending |
| 3-01-02 | 01 | 1 | WRIT-02 | unit negative path | `uv run pytest tests/test_write.py::test_block_append_missing_page_raises_explicit_error -x -q` | ❌ Wave 1 | ⬜ pending |
| 3-01-03 | 01 | 1 | WRIT-04 | unit negative path | `uv run pytest tests/test_write.py::test_block_update_missing_uuid_raises_explicit_error -x -q` | ❌ Wave 1 | ⬜ pending |
| 3-01-04 | 01 | 1 | WRIT-05 | unit negative path | `uv run pytest tests/test_write.py::test_block_delete_missing_uuid_raises_explicit_error -x -q` | ❌ Wave 1 | ⬜ pending |
| 3-02-01 | 02 | 2 | WRIT-01 | unit + state readback | `uv run pytest tests/test_write.py::test_page_create_with_properties_and_initial_blocks -x -q` | ❌ Wave 1 | ⬜ pending |
| 3-02-02 | 02 | 2 | WRIT-02 | unit | `uv run pytest tests/test_write.py::test_block_append_accepts_strings_and_nested_objects -x -q` | ❌ Wave 1 | ⬜ pending |
| 3-02-03 | 02 | 2 | WRIT-03 | unit + hierarchy readback | `uv run pytest tests/test_write.py::test_block_append_preserves_requested_hierarchy_and_order -x -q` | ❌ Wave 1 | ⬜ pending |
| 3-03-01 | 03 | 3 | WRIT-04 | unit + state readback | `uv run pytest tests/test_write.py::test_block_update_changes_content_and_verifies_readback -x -q` | ❌ Wave 1 | ⬜ pending |
| 3-03-02 | 03 | 3 | WRIT-05 | unit + absence verification | `uv run pytest tests/test_write.py::test_block_delete_removes_block_from_followup_reads -x -q` | ❌ Wave 1 | ⬜ pending |
| 3-03-03 | 03 | 3 | WRIT-01..05 | registration / smoke | `uv run pytest tests/test_server.py -q` | ✅ existing | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 1 Requirements

- [ ] `tests/test_write.py` — red-state stubs for WRIT-01 through WRIT-05
- [ ] `tests/test_write.py` — missing-page and missing-UUID red-state tests
- [ ] Shared mock helpers for nested write payloads and read-after-write assertions

*Existing infrastructure already covers pytest, asyncio, and base MCP context patterns.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Page properties appear correctly in the Logseq UI after `page_create` | WRIT-01 | Unit tests can confirm RPC args and readback, but not UI rendering semantics | Create a page with representative properties, inspect it in Logseq, and confirm properties render at page level rather than as plain block text |
| Nested append order matches visible editor hierarchy | WRIT-03 | Readback validates structure, but live Logseq behavior can still differ on insert ordering | Append a mixed nested payload to a disposable page, refresh Logseq, and confirm sibling order plus parent/child placement visually |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 1 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 1 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
