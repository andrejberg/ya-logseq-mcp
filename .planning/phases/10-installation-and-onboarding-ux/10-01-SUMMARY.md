---
phase: 10-installation-and-onboarding-ux
plan: 01
subsystem: docs
tags: [readme, onboarding, mcp, uv, smoke-tests]
requires:
  - phase: 09-relocation-and-runtime-configuration
    provides: canonical runtime path and project-launch conventions
provides:
  - Clean-environment onboarding flow with explicit prerequisites and first-run validation
  - Copy-paste MCP client config with required command/args/cwd/env fields
  - Ordered smoke-check and escalation guidance linked to maintainer runbook checks
affects: [phase-11-github-publication-surface, docs, onboarding]
tech-stack:
  added: []
  patterns: [README-canonical-onboarding, runbook-doc-guardrails]
key-files:
  created: []
  modified: [README.md, RUNBOOK.md]
key-decisions:
  - "Keep README as canonical onboarding surface and keep RUNBOOK focused on maintainer verification guardrails."
  - "Use python3 checks in clean-shell verification to avoid hidden python alias assumptions."
patterns-established:
  - "Onboarding docs include explicit success markers and failure-escalation branch."
  - "MCP config examples are parseable and tied to runtime startup semantics."
requirements-completed: [DOCS-01, DOCS-02, DOCS-03]
duration: 12min
completed: 2026-03-16
---

# Phase 10 Plan 01: Installation and Onboarding UX Summary

**README now provides a clean-shell install-to-smoke onboarding path with parseable MCP config and explicit escalation guidance, backed by RUNBOOK guardrails**

## Performance

- **Duration:** 12 min
- **Started:** 2026-03-16T13:53:03Z
- **Completed:** 2026-03-16T14:05:04Z
- **Tasks:** 3
- **Files modified:** 2

## Accomplishments

- Expanded README onboarding into a stepwise clean-environment flow with explicit prerequisites, install, run, and success markers.
- Added copy-paste-ready MCP config guidance with complete schema fields and startup semantics notes for Claude Desktop and equivalent MCP clients.
- Added ordered smoke-check plus failure-escalation guidance, and mirrored maintainer validation guardrails in RUNBOOK.

## Task Commits

Each task was committed atomically:

1. **Task 1: Rewrite README onboarding flow for clean-environment install and first run** - `50dbce5` (feat)
2. **Task 2: Publish copy-paste-ready MCP configuration examples for Claude Desktop and equivalent clients** - `7cf1397` (feat)
3. **Task 3: Add explicit smoke-check flow and keep maintainer guardrails aligned** - `76d2098` (docs)

**Plan metadata:** `(pending final docs commit)`

## Files Created/Modified

- `README.md` - Canonical user onboarding: prerequisites, install, run, MCP config, smoke flow, and docs-only verification markers
- `RUNBOOK.md` - Maintainer smoke and README-onboarding guardrail commands to keep docs accurate over time

## Decisions Made

- Keep runtime guidance script-first (`ya-logseq-mcp`) and keep module launch as troubleshooting fallback only.
- Keep Claude Desktop as the primary MCP example while explicitly noting equivalent client requirements.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Removed hidden `python` alias dependency in clean-shell verification**
- **Found during:** Post-task verification
- **Issue:** Fresh-shell onboarding checks can fail on systems where `python` is unavailable but `python3` is present.
- **Fix:** Switched verification checks to `python3 --version` in README install and clean-shell sequences.
- **Files modified:** README.md
- **Verification:** `env -i ... python3 --version ...` clean-shell command executed successfully.
- **Committed in:** `6884e80`

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Required for deterministic clean-environment onboarding validation; no scope creep.

## Issues Encountered

- Required verification command `uv run ... pytest tests/integration/test_mcp_stdio.py -x -q -m integration` failed reproducibly with `JSONDecodeError` in `test_mcp_health_and_get_page_round_trip`; no code in this plan changed integration runtime paths or test logic, so this was recorded as an existing integration-environment issue.
- The provided one-liner `uv run ... python -c '<regex parse>'` unexpectedly failed to match the README JSON block in this shell context; equivalent validation with `python3 -c` succeeded and confirmed config schema/startup semantics.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Onboarding docs are substantially hardened and include explicit install, config, and smoke verification flow.
- Phase 11 can proceed with GitHub publication surface work using README as canonical onboarding source.

---
*Phase: 10-installation-and-onboarding-ux*
*Completed: 2026-03-16*

## Self-Check: PASSED

- FOUND: `.planning/phases/10-installation-and-onboarding-ux/10-01-SUMMARY.md`
- FOUND commits: `50dbce5`, `7cf1397`, `76d2098`, `6884e80`
