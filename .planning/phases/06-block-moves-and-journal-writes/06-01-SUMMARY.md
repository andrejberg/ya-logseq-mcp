---
phase: 06-block-moves-and-journal-writes
plan: 01
subsystem: api
tags: [logseq, mcp, move-block, stdio, testing]
requires:
  - phase: 04-integration-and-swap
    provides: isolated graph fixtures, stdio transport harness, and parity-safe live verification patterns
  - phase: 05-lifecycle-write-semantics
    provides: disposable page lifecycle helpers reused for Phase 6 move fixtures
provides:
  - public move_block tool with whole-tree readback verification
  - unit coverage for before, after, child, and explicit failure paths
  - disposable move-page fixtures for live and stdio transport tests
affects: [phase-06-journal-tools, write-tools, integration-tests]
tech-stack:
  added: []
  patterns: [whole-tree mutation verification, disposable live-test pages, MCP stdio round-trip assertions]
key-files:
  created:
    - .planning/phases/06-block-moves-and-journal-writes/06-01-SUMMARY.md
  modified:
    - src/logseq_mcp/tools/write.py
    - tests/test_write.py
    - tests/test_server.py
    - tests/integration/conftest.py
    - tests/integration/test_live_graph.py
    - tests/integration/test_mcp_stdio.py
key-decisions:
  - "Mapped public position strings to Logseq's real moveBlock opts contract: before -> {before: true}, child -> {children: true}, after -> {}."
  - "Kept move success tied to whole-page tree readback so placement and subtree preservation are proved from user-visible structure."
  - "Added disposable Phase 6 move pages instead of mutating Phase 4 parity or sandbox fixtures."
patterns-established:
  - "Mutation verification pattern: preflight source and target, capture subtree UUIDs, mutate, then prove structure from page-tree readback."
  - "Live move coverage pattern: create disposable pages with deterministic source/anchor layout and delete them after each test."
requirements-completed: [WRIT-08]
duration: 18min
completed: 2026-03-12
---

# Phase 6 Plan 1: Move Block Summary

**`move_block` now supports before, after, and child placement with subtree-preserving readback verification across unit, live isolated-graph, and MCP stdio transport coverage.**

## Performance

- **Duration:** 18 min
- **Started:** 2026-03-12T13:46:51Z
- **Completed:** 2026-03-12T14:04:51Z
- **Tasks:** 2
- **Files modified:** 6

## Accomplishments
- Added `move_block` plus helper logic that captures the moved subtree UUID set and verifies the moved root appears exactly once in the requested relationship after readback.
- Extended unit coverage to prove `before`, `after`, and `child` semantics plus explicit failures for invalid positions, missing blocks, and subtree-loss verification failures.
- Added disposable Phase 6 move-page fixtures and proved `move_block` through both direct live calls and the production stdio entrypoint.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add move-block unit coverage and subtree verification helpers** - `d059f07` (test)
2. **Task 1: Add move-block unit coverage and subtree verification helpers** - `26d239d` (feat)
3. **Task 2: Register move_block and prove it on the isolated graph and MCP stdio transport** - `4b6177d` (feat)

_Note: Task 1 followed TDD with separate RED and GREEN commits._

## Files Created/Modified
- `src/logseq_mcp/tools/write.py` - Added move validation, subtree UUID capture, whole-tree readback checks, and the public `move_block` handler.
- `tests/test_write.py` - Added unit coverage for move placement, subtree preservation, and explicit negative cases.
- `tests/test_server.py` - Extended tool-registry coverage to include `move_block`.
- `tests/integration/conftest.py` - Added disposable Phase 6 move-page setup helpers on top of the isolated graph lifecycle harness.
- `tests/integration/test_live_graph.py` - Added live isolated-graph coverage for `before`, `after`, and `child` moves.
- `tests/integration/test_mcp_stdio.py` - Added stdio registry coverage and end-to-end `move_block` round-trip verification.

## Decisions Made
- Used Logseq's observed `moveBlock` opts contract instead of the planned string-only third argument because live probing showed `before` and `child` require structured options to work correctly.
- Verified moves from `getPageBlocksTree` rather than trusting RPC return payloads because `moveBlock` returns `null` on the installed Logseq build.
- Reused lifecycle page cleanup for Phase 6 move fixtures so destructive tests stay disposable and deterministic.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected the live `moveBlock` RPC contract**
- **Found during:** Task 2 (Register move_block and prove it on the isolated graph and MCP stdio transport)
- **Issue:** The planned `(moved_uuid, target_uuid, position-string)` assumption did not match the installed Logseq build. `before` and `child` were ineffective or behaved like no-ops.
- **Fix:** Switched the internal RPC call to Logseq's actual options contract: `before -> {"before": true}`, `child -> {"children": true}`, `after -> {}` while preserving the public `move_block(uuid, target_uuid, position)` API.
- **Files modified:** `src/logseq_mcp/tools/write.py`, `tests/test_write.py`
- **Verification:** `uv run pytest tests/test_write.py -x -q`; `source ~/Workspace/.env && uv run pytest tests/integration/test_live_graph.py -x -q -m integration`; `source ~/Workspace/.env && uv run pytest tests/integration/test_mcp_stdio.py -x -q -m integration`
- **Committed in:** `4b6177d` (part of task commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** The auto-fix was required for correctness on the real Logseq build. No scope creep.

## Issues Encountered
- The first live `before` and `after` attempts exposed that `moveBlock` does not follow the assumed string-position contract. A targeted disposable-page probe established the real behavior and unblocked the plan without changing the public tool shape.

## User Setup Required

None - no external service configuration required beyond the existing isolated graph and `~/Workspace/.env` setup already documented for integration tests.

## Next Phase Readiness
- Phase 6 now has a reusable move-page fixture pattern and a proven mutation-verification contract for future journal write work.
- No blockers remain for the remaining Phase 6 plans.

## Self-Check: PASSED

- Verified summary file exists at `.planning/phases/06-block-moves-and-journal-writes/06-01-SUMMARY.md`
- Verified task commits exist: `d059f07`, `26d239d`, `4b6177d`
