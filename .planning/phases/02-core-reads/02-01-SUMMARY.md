---
phase: 02-core-reads
plan: 01
subsystem: testing
tags: [pytest, tdd, async, mcp, logseq]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: AppContext, LogseqClient, BlockEntity/PageEntity types, health tool
provides:
  - "6 failing async test stubs covering get_page dedup, nesting, API arg, get_block, list_pages namespace filter, get_references parsing (RED state for TDD)"
affects: ["02-02", "02-03"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Import tools inside test body so pytest collects all tests even when impl is missing"
    - "_collect_uuids() recursive helper for UUID deduplication assertions"
    - "_make_ctx() helper to build mock AppContext for tool tests"

key-files:
  created:
    - tests/test_core.py
  modified: []

key-decisions:
  - "Import inside test body (not module-level) to allow collection of all 6 tests even when tools/core.py lacks the symbols"
  - "Fully-specified assertions (not `pass` stubs) so executor in Plan 02 implements against real expectations"
  - "token_env fixture replicated from test_server.py for consistency"

patterns-established:
  - "TDD RED: import inside test body pattern for missing-impl isolation"
  - "AsyncMock-based mock context pattern: _make_ctx(fake_call) helper"

requirements-completed: [READ-01, READ-02, READ-03, READ-04, READ-05, READ-06]

# Metrics
duration: 3min
completed: 2026-03-09
---

# Phase 2 Plan 01: Core Reads Test Scaffold Summary

**6 fully-specified async test stubs for get_page dedup/nesting/args, get_block, list_pages namespace filter, and get_references — all failing (RED) awaiting implementation in Plan 02**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-09T21:59:29Z
- **Completed:** 2026-03-09T22:02:00Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments
- Created tests/test_core.py with 6 async test functions covering READ-01 through READ-06
- All 6 tests fail with ImportError (RED state) — tools not yet implemented
- Existing 18 tests in test_server.py and test_client.py still pass (no regression)

## Task Commits

Each task was committed atomically:

1. **Task 1: Write test_core.py with 6 failing stubs** - `97694a3` (test)

## Files Created/Modified
- `tests/test_core.py` - 6 async test stubs: test_get_page_no_duplicate_uuids, test_get_page_nesting_correct, test_get_page_uses_name, test_get_block_returns_block, test_list_pages_namespace_filter, test_get_references_parses_response

## Decisions Made
- Import tools inside test body (not at module level): allows pytest to collect all 6 tests even when the import fails, avoiding a single ImportError from silently killing all test collection
- Fully-specified assertions rather than `pass` stubs: executor for Plan 02 implements against exact expectations already written

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- tests/test_core.py is ready; Plan 02 (implement tools) runs `uv run pytest tests/test_core.py -x -q` against each tool as it is written
- Implementation target: all 6 tests go GREEN after Plan 02 completes

---
*Phase: 02-core-reads*
*Completed: 2026-03-09*
