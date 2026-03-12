# v1.1 Pitfalls Research

## Main Risks

| Area | Pitfall | Prevention |
|------|---------|------------|
| Journals | Guessing journal page names instead of resolving stable journal metadata | Prefer `journal-day` / journal metadata where possible; keep page-name guessing as fallback only |
| `journal_append` | Breaking child hierarchy by bypassing existing append helpers | Reuse Phase 3 normalization and append/readback helpers |
| `journal_range` | Implementing one guessed page lookup per day across large ranges | Use constrained DataScript or other metadata-based lookup to avoid slow sequential probing |
| `delete_page` | Trusting RPC success without verifying absence | Confirm the page no longer resolves and no longer appears in page listings |
| `rename_page` | Testing only simple page names | Include namespaced pages and backlink-sensitive cases |
| `move_block` | Verifying destination only and forgetting source removal or subtree integrity | Assert source absence, destination presence, and preserved children/order |
| All six tools | Overfitting to mocked payloads | Reuse isolated live graph validation before milestone sign-off |
| Destructive tests | Mutating the daily-driver graph | Keep destructive checks inside the isolated graph harness only |

## Warning Signs

- A tool is treated as complete without follow-up readback.
- Tests cover only simple page names and flat blocks.
- `journal_range` loops through guessed names per day without metadata support.
- `move_block` tests ignore subtree preservation.
- Destructive tests are not fenced to the isolated graph.

## Phase Guidance

- Early phase: settle shared mutation verification and lifecycle semantics.
- Journal phase: settle date parsing and journal resolution before building range reads.
- Integration phase: prove namespaced rename flows, destructive safety, and journal behavior on the isolated graph.
