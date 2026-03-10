---
phase: 04-integration-and-swap
plan: 01
subsystem: testing
tags: [pytest, logseq, integration, fixtures, live-api]
requires:
  - phase: 03-write-tools
    provides: live write tools and server tool registration used by the Phase 4 harness
provides:
  - isolated graph env guards and fixture seeding helpers for live integration runs
  - deterministic parity and sandbox fixture pages for the disposable Logseq graph
  - opt-in live tests covering graph isolation and sandbox-only append/update/delete flows
  - write-tool handling for Logseq update/delete RPCs that return null on success
affects: [04-02-PLAN.md, 04-03-PLAN.md, tests/integration]
tech-stack:
  added: []
  patterns: [opt-in live pytest marker, isolated graph guard before mutation, readback-first verification for null Logseq write RPCs]
key-files:
  created:
    - tests/integration/conftest.py
    - tests/integration/test_live_graph.py
    - tests/fixtures/graph/README.md
    - tests/fixtures/graph/pages/parity-page.md
    - tests/fixtures/graph/pages/write-sandbox.md
  modified:
    - pyproject.toml
    - src/logseq_mcp/tools/write.py
    - tests/test_write.py
key-decisions:
  - "Phase 4 live tests stay behind pytest's `integration` marker and require `source ~/Workspace/.env` plus the isolated `logseq-test-graph`."
  - "The harness resets only `Phase 04 Write Sandbox` before destructive checks and leaves the parity page read-only."
  - "Live write success is determined by follow-up readback because Logseq returns null from `updateBlock` and `removeBlock` even when the mutation succeeds."
patterns-established:
  - "Isolated graph contract: assert active graph name before the first live mutation."
  - "Disposable sandbox pattern: reseed a reserved page to a known baseline before each destructive run."
  - "Live API normalization: treat write RPC return values as advisory and verify via follow-up reads."
requirements-completed: [INTG-02]
duration: 10min
completed: 2026-03-10
---

# Phase 4 Plan 1: Isolated Graph Safety Harness Summary

**Opt-in live pytest coverage for an isolated Logseq graph with deterministic parity fixtures, sandbox-only mutations, and readback-verified write RPC handling**

## Performance

- **Duration:** 10 min
- **Started:** 2026-03-10T08:31:00Z
- **Completed:** 2026-03-10T08:40:55Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- Added the reusable isolated-graph harness in `tests/integration/conftest.py` plus committed parity and sandbox fixture content under `tests/fixtures/graph/`.
- Added live integration tests that fail fast on the wrong graph, verify fixture page presence, and exercise append/update/delete only on the reserved sandbox page.
- Fixed the write tools to accept Logseq's live `null` responses for `updateBlock` and `removeBlock` when readback confirms the mutation succeeded.

## Task Commits

Each task was committed atomically:

1. **Task 1: Build isolated graph fixtures and opt-in integration test plumbing** - `017182a` (feat)
2. **Task 2: Add live graph safety and sandbox verification tests** - `293c6b9` (fix)

## Files Created/Modified
- `tests/integration/conftest.py` - loads live env, asserts the isolated graph, seeds the sandbox baseline, and exposes helpers for live tests.
- `tests/integration/test_live_graph.py` - covers graph isolation, fixture presence, and sandbox-only append/update/delete flows.
- `tests/fixtures/graph/README.md` - documents the disposable graph contract and live-test setup.
- `tests/fixtures/graph/pages/parity-page.md` - defines the deterministic nested parity page used in later Phase 4 checks.
- `tests/fixtures/graph/pages/write-sandbox.md` - defines the reserved mutation target for destructive live checks.
- `pyproject.toml` - registers the opt-in `integration` pytest marker.
- `src/logseq_mcp/tools/write.py` - switches update/delete success checks to follow-up readback instead of trusting null RPC payloads.
- `tests/test_write.py` - locks in the null-response behavior for update/delete with unit coverage.

## Decisions Made
- Kept live integration work explicit behind `pytest -m integration` so the default fast test loop stays untouched.
- Reset the sandbox page to a fixed baseline before each destructive test instead of mutating arbitrary pages or the parity fixture.
- Treated Logseq's live null mutation responses as successful only when subsequent reads prove the expected state change.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Accepted null `updateBlock` responses when readback proves success**
- **Found during:** Task 2 (Add live graph safety and sandbox verification tests)
- **Issue:** The live Logseq API returned `null` from `logseq.Editor.updateBlock` even though the block content changed correctly.
- **Fix:** Removed the raw-response success requirement and relied on the existing follow-up block readback.
- **Files modified:** `src/logseq_mcp/tools/write.py`, `tests/test_write.py`
- **Verification:** `uv run pytest tests/test_write.py -q`; `source ~/Workspace/.env && uv run pytest tests/integration/test_live_graph.py -x -q -m integration`
- **Committed in:** `293c6b9`

**2. [Rule 1 - Bug] Accepted null `removeBlock` responses when absence checks prove success**
- **Found during:** Task 2 (Add live graph safety and sandbox verification tests)
- **Issue:** The live Logseq API returned `null` from `logseq.Editor.removeBlock` while the block was actually deleted.
- **Fix:** Removed the raw-response success requirement and kept the existing absence verification as the authoritative check.
- **Files modified:** `src/logseq_mcp/tools/write.py`, `tests/test_write.py`
- **Verification:** `uv run pytest tests/test_write.py -q`; `source ~/Workspace/.env && uv run pytest tests/integration/test_live_graph.py -x -q -m integration`
- **Committed in:** `293c6b9`

---

**Total deviations:** 2 auto-fixed (2 bug fixes)
**Impact on plan:** Both fixes were necessary to make the planned live sandbox verification reflect real Logseq behavior. No scope creep beyond the proven integration defects.

## Issues Encountered
- The disposable `logseq-test-graph` was missing the committed parity and sandbox pages at the start of verification. Reseeding the local graph's `pages/` directory from `tests/fixtures/graph/pages/` resolved the environment drift.

## User Setup Required

None - no new external service configuration beyond the existing `source ~/Workspace/.env` and opening the isolated `logseq-test-graph`.

## Next Phase Readiness
- Phase 4 now has concrete isolated-graph guards and live write evidence, so `04-02` can focus on black-box MCP stdio verification without risking the daily-driver graph.
- The committed parity fixture page is in place for the later graphthulhu comparison work in `04-03`.

## Self-Check: PASSED
- Found `.planning/phases/04-integration-and-swap/04-01-SUMMARY.md`
- Found task commit `017182a`
- Found task commit `293c6b9`

---
*Phase: 04-integration-and-swap*
*Completed: 2026-03-10*
