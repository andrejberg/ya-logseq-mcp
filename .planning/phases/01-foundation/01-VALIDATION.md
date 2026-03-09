---
phase: 1
slug: foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-09
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 + pytest-asyncio 1.3.0 |
| **Config file** | `pyproject.toml` — `[tool.pytest.ini_options]` section (Wave 0 installs) |
| **Quick run command** | `uv run pytest tests/ -x -q` |
| **Full suite command** | `uv run pytest tests/ -v` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `uv run pytest tests/ -x -q`
- **After every plan wave:** Run `uv run pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 1-??-01 | 01 | 0 | FOUN-01 | unit | `uv run pytest tests/test_client.py::test_auth_header -x` | ❌ W0 | ⬜ pending |
| 1-??-02 | 01 | 0 | FOUN-02 | unit | `uv run pytest tests/test_client.py::test_retry -x` | ❌ W0 | ⬜ pending |
| 1-??-03 | 01 | 0 | FOUN-03 | unit | `uv run pytest tests/test_client.py::test_semaphore -x` | ❌ W0 | ⬜ pending |
| 1-??-04 | 01 | 0 | FOUN-04 | unit | `uv run pytest tests/test_types.py -x` | ❌ W0 | ⬜ pending |
| 1-??-05 | 01 | 1 | FOUN-05 | unit | `uv run pytest tests/test_server.py::test_tool_registered -x` | ❌ W0 | ⬜ pending |
| 1-??-06 | 01 | 1 | FOUN-06 | unit | `uv run pytest tests/test_server.py::test_stderr_only -x` | ❌ W0 | ⬜ pending |
| 1-??-07 | 01 | 1 | FOUN-07 | manual | Manual — requires live Logseq | N/A | ⬜ pending |
| 1-??-08 | 01 | 1 | FOUN-08 | unit | `uv run pytest tests/test_server.py::test_lifespan -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_client.py` — stubs for FOUN-01, FOUN-02, FOUN-03
- [ ] `tests/test_types.py` — stubs for FOUN-04
- [ ] `tests/test_server.py` — stubs for FOUN-05, FOUN-06, FOUN-08
- [ ] `tests/conftest.py` — shared fixtures (httpx mock, FastMCP test client)
- [ ] `pyproject.toml` `[tool.pytest.ini_options]` with `asyncio_mode = "auto"`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `health` returns graph name + page count | FOUN-07 | Requires live Logseq instance with API enabled | Run `uv run python -m logseq_mcp`, call health tool, verify graph name and page count in response |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
