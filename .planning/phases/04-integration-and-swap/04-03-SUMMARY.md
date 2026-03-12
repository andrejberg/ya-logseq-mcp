---
phase: 04-integration-and-swap
plan: 03
subsystem: testing
tags: [pytest, mcp, graphthulhu, parity, rollout]
requires:
  - phase: 04-integration-and-swap
    provides: stdio transport verification and isolated graph fixtures from Plans 01-02
provides:
  - structural graphthulhu parity coverage for `get_page` on the fixed fixture page
  - shared-workspace rollout runbook for side-by-side `logseq-mcp` validation with graphthulhu retained as fallback
  - namespaced-page hardening so `list_pages` works on the daily-driver graph during rollout
affects: [tests/integration, tests/test_core.py, tests/test_types.py, tests/fixtures/graph/README.md, .planning/STATE.md, .planning/ROADMAP.md]
tech-stack:
  added: []
  patterns: [cross-server parity normalization, manual rollout gate, namespace-ref coercion]
key-files:
  created:
    - tests/integration/test_graphthulhu_parity.py
    - .planning/phases/04-integration-and-swap/04-03-SUMMARY.md
  modified:
    - tests/integration/conftest.py
    - tests/fixtures/graph/README.md
    - src/logseq_mcp/types.py
    - tests/test_core.py
    - tests/test_types.py
    - .planning/STATE.md
    - .planning/ROADMAP.md
key-decisions:
  - "Parity checks stay structural: page identity, top-level order, recursive UUID uniqueness, expected child nesting, and equal-or-fewer total blocks than graphthulhu."
  - "Graphthulhu remains in `~/Workspace/.mcp.json` during rollout so manual validation can target `logseq-mcp` by name without removing the fallback path."
  - "PageEntity coerces namespace page refs like `{'id': N}` to strings so `list_pages` does not fail on namespaced production pages."
patterns-established:
  - "Cross-server payload pattern: parity helpers must accept both FastMCP `structuredContent.result` payloads and raw text JSON payloads."
  - "Rollout gate pattern: complete planning sign-off only after automated parity evidence and manual isolated plus daily-driver smoke checks both pass."
requirements-completed: [INTG-03]
duration: 8min
completed: 2026-03-12
---

# Phase 4 Plan 3: Parity and Rollout Summary

**Graphthulhu parity is automated, the shared-config rollout gate passed, and the daily-driver namespaced-page bug found during smoke validation is fixed**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-12T11:52:00Z
- **Completed:** 2026-03-12T12:00:00Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Added structural parity integration coverage that compares `logseq-mcp` and graphthulhu on the fixed parity fixture page while proving the deduplication win without breaking block nesting.
- Updated the isolated-graph fixture runbook with the shared workspace MCP config prerequisite and the side-by-side rollout procedure that keeps graphthulhu available as fallback.
- Fixed `list_pages` for daily-driver graphs where Logseq returns `namespace` as a page-ref object, then added regression coverage so the rollout smoke test can pass on namespaced graphs.
- Recorded the completed manual gate after the isolated `logseq-test-graph` smoke test and the daily-driver read-only validation both passed against `logseq-mcp`.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add structural parity tests against graphthulhu on the fixed fixture page** - `9ccc58b`, `6614460`, `5b7ffbb` (feat/test/feat)
2. **Task 2: Execute the side-by-side manual smoke gate and record sign-off** - `PENDING_COMMIT` (fix)

## Files Created/Modified
- `tests/integration/conftest.py` - adds the graphthulhu MCP session and parity-test environment hooks used by the new integration coverage.
- `tests/integration/test_graphthulhu_parity.py` - verifies structural parity, deduplicated UUIDs, and expected nesting on the parity fixture page.
- `tests/fixtures/graph/README.md` - documents the shared-config prerequisite, parity command, and manual side-by-side rollout gate.
- `src/logseq_mcp/types.py` - coerces namespace page refs so namespaced production pages do not break `list_pages`.
- `tests/test_core.py` and `tests/test_types.py` - lock in the namespace-ref regression fix.
- `.planning/STATE.md` and `.planning/ROADMAP.md` - mark Phase 4 complete after the manual gate passed.

## Decisions Made
- Kept parity assertions structural instead of byte-identical so the comparison tolerates payload-shape differences between FastMCP and graphthulhu while still proving the user-visible deduplication contract.
- Preserved graphthulhu in the shared workspace config throughout validation so rollout can fail safely without disabling the existing daily-driver path.
- Fixed the namespaced-page bug in the model layer rather than adding list-pages-specific exception handling so any future page validation path inherits the same tolerance.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Parity helpers had to decode graphthulhu raw JSON text responses**
- **Found during:** Task 1 (Add structural parity tests against graphthulhu on the fixed fixture page)
- **Issue:** graphthulhu returns plain text JSON instead of FastMCP `structuredContent`, so the first parity helper only worked against `logseq-mcp`.
- **Fix:** Updated the parity helper to decode either payload shape before normalization.
- **Files modified:** `tests/integration/test_graphthulhu_parity.py`
- **Verification:** `source ~/Workspace/.env && uv run pytest tests/integration/test_graphthulhu_parity.py -x -q -m integration`
- **Committed in:** `5b7ffbb`

**2. [Rule 3 - Blocking] Daily-driver `list_pages` failed on namespaced pages**
- **Found during:** Task 2 (Execute the side-by-side manual smoke gate and record sign-off)
- **Issue:** Logseq returned `namespace` as `{'id': 2393}` for a namespaced page, which violated `PageEntity.namespace: str` and made `list_pages` unusable on the production graph.
- **Fix:** Coerced namespace page refs to strings in `PageEntity` and added regression tests that cover the production payload shape.
- **Files modified:** `src/logseq_mcp/types.py`, `tests/test_core.py`, `tests/test_types.py`
- **Verification:** `uv run pytest tests/test_types.py tests/test_core.py -q` and `uv run pytest tests/ -v -m "not integration"`
- **Committed in:** `PENDING_COMMIT`

---

**Total deviations:** 2 auto-fixed (2 blocking)
**Impact on plan:** Both fixes were required to complete the intended rollout gate on a real shared workspace configuration. No scope creep.

## Issues Encountered
- The daily-driver graph contains namespaced pages whose `namespace` field comes back as a page-ref object rather than a string, which was invisible in the isolated graph until the manual smoke test exercised the real workspace.

## User Setup Required

Keep both `logseq-mcp` and graphthulhu configured in `~/Workspace/.mcp.json` until a later cleanup phase explicitly removes the fallback entry.

## Next Phase Readiness
- Phase 4 is complete: automated parity evidence, isolated smoke validation, and daily-driver validation all passed.
- The project is ready for milestone completion or cleanup work that removes the temporary graphthulhu fallback when desired.

## Self-Check: PASSED
- Found `.planning/phases/04-integration-and-swap/04-03-SUMMARY.md`
- Found task commits `9ccc58b`, `6614460`, and `5b7ffbb`
- Verified daily-driver `list_pages` after the namespace-ref fix

---
*Phase: 04-integration-and-swap*
*Completed: 2026-03-12*
