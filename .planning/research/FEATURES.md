# v1.1 Feature Research

## Table Stakes

### Journals

- `journal_today` returns today's journal page and creates it if missing.
- `journal_append` accepts a `YYYY-MM-DD` date and appends blocks using the same nested block contract as `block_append`.
- `journal_range` accepts `from` and `to` dates, rejects invalid or reversed ranges, and returns the journal entries for matching days.

### Lifecycle Writes

- `delete_page` deletes a page by name.
- `rename_page` renames a page by old and new name and relies on Logseq to update links.
- `move_block` moves a block by UUID relative to another block with `before`, `after`, or `child` positioning.

### Shared Expectations

- All six tools stay stateless and operate directly against Logseq.
- All tools return explicit MCP errors for invalid input or missing targets.
- Journal and move operations preserve block-tree structure; moves are not copies.

## Edge Cases To Cover

- Journal pages may resolve under multiple naming formats if metadata lookup is unavailable.
- `journal_today` must create the page on first use of the day.
- `journal_range` can miss valid journals if it relies only on guessed names.
- `rename_page` needs clear behavior for nonexistent pages and name collisions.
- `move_block` must preserve subtree integrity and destination ordering.
- Destructive operations must verify final graph state instead of trusting null/ambiguous mutation returns.

## Differentiators To Defer

- Smarter journal resolution and lookup caching
- Richer mutation verification output beyond lean payloads
- Natural-language date handling
- Search-like journal summaries
- Expanded query tooling

## Anti-Features For v1.1

- Brute-force scan-all-pages logic
- Content parsing or enrichment
- Local cache or in-memory graph analysis
- Any spillover into templates, kanban, or general queries
