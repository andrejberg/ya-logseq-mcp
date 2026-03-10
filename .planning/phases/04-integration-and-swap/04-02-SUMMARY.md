---
phase: 04-integration-and-swap
plan: 02
subsystem: testing
tags: [pytest, mcp, stdio, logseq, integration]
requires:
  - phase: 04-integration-and-swap
    provides: isolated graph env guards and live fixture seeding from Plan 01
provides:
  - black-box stdio subprocess coverage for the production `python -m logseq_mcp` entrypoint
  - MCP transport checks for tool discovery plus read and write round trips
  - stderr-vs-stdout hygiene assertions for the production server logging path
affects: [04-03-PLAN.md, tests/integration]
tech-stack:
  added: []
  patterns: [subprocess-backed MCP session fixture, live stdio round-trip verification, stderr protocol hygiene assertion]
key-files:
  created:
    - tests/integration/test_mcp_stdio.py
  modified:
    - tests/integration/conftest.py
    - tests/integration/test_mcp_stdio.py
key-decisions:
  - "The stdio harness launches `uv run python -m logseq_mcp` directly so transport coverage matches the production Claude entrypoint."
  - "Live graph safety stays enforced by reusing Plan 01 fixture seeding before any MCP write call instead of inventing a second isolation contract."
  - "MCP tool assertions parse the real `structuredContent.result` wrapper emitted by FastMCP rather than assuming raw JSON text only."
patterns-established:
  - "Production-entrypoint harness: subprocess integration tests must speak to `python -m logseq_mcp` over stdio instead of importing the server in-process."
  - "Transport readback pattern: verify write tools through follow-up MCP reads, not direct Python helpers."
requirements-completed: [INTG-01, INTG-02]
duration: 26min
completed: 2026-03-10
---

# Phase 4 Plan 2: Stdio Transport Summary

**Production `python -m logseq_mcp` verified as a real MCP stdio server with tool discovery, live read/write round trips, and stderr-only logging**

## Performance

- **Duration:** 26 min
- **Started:** 2026-03-10T08:44:00Z
- **Completed:** 2026-03-10T09:10:40Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Added a reusable subprocess-backed MCP session harness that launches the production stdio entrypoint with the live Logseq test environment.
- Added black-box MCP transport tests for tool discovery, `health`, `get_page`, and a guarded sandbox append/update/delete round trip.
- Proved the production server keeps logging on `stderr` while stdio protocol traffic remains clean enough for end-to-end MCP calls.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add reusable subprocess and MCP session helpers for stdio integration** - `2dae122` (feat)
2. **Task 2: Add black-box stdio transport tests for startup, tool calls, and stdout hygiene** - `28ab027` (feat)

## Files Created/Modified
- `tests/integration/conftest.py` - adds the reusable stdio subprocess launcher, MCP session fixture, and stderr protocol hygiene assertion.
- `tests/integration/test_mcp_stdio.py` - exercises the production MCP stdio server for tool discovery, health/get_page round trips, sandbox writes, and logging hygiene.

## Decisions Made
- Kept the stdio harness in `tests/integration/` and launched `uv run python -m logseq_mcp` directly to preserve black-box coverage of the real server entrypoint.
- Reused the existing isolated graph setup from Plan 01 before the MCP write test so transport coverage cannot mutate the wrong graph.
- Parsed FastMCP tool results from `structuredContent.result` first, falling back to text content only when needed, because that matches the live response shape from the installed MCP client.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Switched stderr capture to a real temporary file for stdio subprocesses**
- **Found during:** Task 1 (Add reusable subprocess and MCP session helpers for stdio integration)
- **Issue:** `mcp.client.stdio` passes the stderr target to `subprocess.Popen`, which rejected the initial in-memory buffer because it had no `fileno()`.
- **Fix:** Replaced the in-memory stderr capture with `TemporaryFile(mode="w+")` and kept the helper's readback API the same.
- **Files modified:** `tests/integration/conftest.py`
- **Verification:** `source ~/Workspace/.env && uv run pytest tests/integration/test_mcp_stdio.py::test_stdio_server_exposes_expected_tools -x -q -m integration`
- **Committed in:** `2dae122`

**2. [Rule 3 - Blocking] Parsed FastMCP tool results from the live structured-content wrapper**
- **Found during:** Task 2 (Add black-box stdio transport tests for startup, tool calls, and stdout hygiene)
- **Issue:** Live `call_tool()` responses returned JSON under `structuredContent.result`, so the initial parser misread successful payloads and broke assertions.
- **Fix:** Updated the stdio test helper to decode `structuredContent.result` first and fall back to text content parsing only when necessary.
- **Files modified:** `tests/integration/test_mcp_stdio.py`
- **Verification:** `source ~/Workspace/.env && uv run pytest tests/integration/test_mcp_stdio.py -x -q -m integration`
- **Committed in:** `28ab027`

---

**Total deviations:** 2 auto-fixed (2 blocking)
**Impact on plan:** Both fixes were required to complete the planned black-box stdio verification against the real MCP client/server stack. No scope creep.

## Issues Encountered
- The live parity page name is normalized to lowercase in the MCP payload's `page.name`, so the get-page assertion uses case-insensitive comparison while still checking the correct fixture identity.

## User Setup Required

None - no new external service configuration beyond the existing `source ~/Workspace/.env` and isolated `logseq-test-graph` setup.

## Next Phase Readiness
- Phase 4 now has proven stdio transport coverage for the production server, so Plan `04-03` can focus on graphthulhu parity instead of bootstrap or logging concerns.
- The reusable stdio harness can support any later smoke checks that need real MCP transport instead of in-process tool calls.

## Self-Check: PASSED
- Found `.planning/phases/04-integration-and-swap/04-02-SUMMARY.md`
- Found task commit `2dae122`
- Found task commit `28ab027`

---
*Phase: 04-integration-and-swap*
*Completed: 2026-03-10*
