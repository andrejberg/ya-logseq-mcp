# v1.1 Research Summary

## Stack Additions

- No new external dependencies are required for `v1.1`.
- A narrow internal DataScript path may be justified for `journal_range`, but general query tools remain out of scope.

## Table Stakes

- Ship the full journal trio: `journal_today`, `journal_append`, `journal_range`
- Ship the remaining lifecycle writes: `delete_page`, `rename_page`, `move_block`
- Keep the server stateless and reuse the existing FastMCP + Logseq client architecture
- Keep write verification based on readback, not mutation return payloads

## Watch Outs

- Journal lookup should prefer stable metadata over guessed page names where feasible.
- `move_block` and destructive writes need explicit post-mutation verification.
- Namespaced pages must be part of rename coverage.
- Destructive integration tests must stay inside the isolated graph harness.

## Scoping Decision

`v1.1` should include only the six agreed tools. DataScript query tools and template tools stay deferred to `v1.2+`.
