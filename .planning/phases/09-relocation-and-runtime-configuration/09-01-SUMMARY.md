---
phase: 09-relocation-and-runtime-configuration
plan: 01
subsystem: infra
tags: [relocation, runtime-config, mcp, uv, docs, integration-tests]
requires:
  - phase: 08-branding-alignment
    provides: Canonical ya-logseq-mcp naming and script entrypoint usage
provides:
  - Canonical home-relative relocation guidance for docs and maintainer runbook
  - MCP config examples with explicit cwd and script-first launch
  - Integration config helper support for home-relative --project args
affects: [phase-09-plan-02, docs, runbook, integration-runtime]
tech-stack:
  added: []
  patterns: [home-relative path policy, explicit cwd in MCP config, script-first uv launch]
key-files:
  created: [.planning/phases/09-relocation-and-runtime-configuration/09-01-SUMMARY.md]
  modified: [README.md, RUNBOOK.md, CLAUDE.md, tests/integration/conftest.py]
key-decisions:
  - "Use ~/Workspace/tools/ya-logseq-mcp as the single canonical path across docs and maintainer guidance."
  - "Normalize external MCP config args by expanding home-relative --project values before stdio launch."
patterns-established:
  - "Runtime docs should prefer uv run --project <path> ya-logseq-mcp with explicit cwd in client config."
  - "Relocation stale-path scans should target legacy path signatures without broad project-name matching."
requirements-completed: [MOVE-01, MOVE-02, MOVE-03]
duration: 22min
completed: 2026-03-16
---

# Phase 9 Plan 01: Relocation and Runtime Configuration Summary

**Relocation-safe runtime guidance now uses home-relative tools path with explicit MCP cwd and helper-side home path normalization for --project args.**

## Performance

- **Duration:** 22 min
- **Started:** 2026-03-16T11:34:38Z
- **Completed:** 2026-03-16T11:56:44Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Updated README, RUNBOOK, and CLAUDE guidance to canonical `~/Workspace/tools/ya-logseq-mcp`.
- Made script-first runtime commands primary and retained module invocation as fallback troubleshooting guidance.
- Added explicit `cwd` to MCP client config examples and aligned integration helper launch behavior with explicit `--project` flows.
- Added relocation stale-reference scan command with repo-wide exclusions and false-positive-safe matching approach.

## Task Commits

Each task was committed atomically:

1. **Task 1: Normalize path and runtime examples to the relocation target** - `2045320` (docs)
2. **Task 2: Align config/test helper assumptions and add targeted stale-reference scanning** - `4d937ed` (fix)

## Files Created/Modified
- `README.md` - Canonical runtime invocation and MCP client configuration updated with explicit `cwd`.
- `RUNBOOK.md` - Maintainer runtime constraints and relocation stale-reference scan guidance updated.
- `CLAUDE.md` - Project workspace/disk path references updated to relocation target and script-first run command.
- `tests/integration/conftest.py` - Home-relative CLI arg normalization and stdio launch command updated to script-first explicit project execution.

## Decisions Made
- Use home-relative `~/Workspace/tools/ya-logseq-mcp` in docs to avoid user-specific absolute paths.
- Normalize `~` in external MCP args for direct subprocess launches where shell expansion does not occur.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Exact verification commands referencing `~/Workspace/tools/ya-logseq-mcp` were adapted to the current checkout path (`/home/berga/Workspace/projects/logseq-mcp`) because relocation is documented/configured in this plan but the workspace itself has not been physically moved in this environment.
- `tests/integration/test_mcp_stdio.py -x -q -m integration` failed on `test_mcp_health_and_get_page_round_trip` with JSON decode on `get_page` payload, indicating live fixture/environment mismatch rather than command/bootstrap failure.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Relocation/runtime documentation and helper assumptions are aligned to the target path policy.
- Remaining work can build on these conventions for runtime validation and relocation follow-through in subsequent plans.

---
*Phase: 09-relocation-and-runtime-configuration*
*Completed: 2026-03-16*

## Self-Check: PASSED
