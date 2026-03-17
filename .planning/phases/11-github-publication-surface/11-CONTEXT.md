# Phase 11: GitHub Publication Surface - Context

**Gathered:** 2026-03-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Publish the renamed project to a public GitHub repository under `github.com/andrej-berg/ya-logseq-mcp` with repository metadata and README content that lets a cold-start GitHub visitor understand, install, and configure the tool. No new MCP features.

</domain>

<decisions>
## Implementation Decisions

### What gets published
- `.planning/` — gitignore and untrack. GSD workflow scaffolding is not useful to external contributors; GitHub Issues is the right contribution surface.
- `logseq-test-graph/` — gitignore and untrack. Local Logseq fixture graph, not portable.
- `CLAUDE.md` — gitignore and untrack. AI-agent operational context with workspace-specific paths; not useful to external users.
- No need to rewrite git history — no sensitive data in tracked history, and the repo hasn't been pushed yet so the public view will be clean after untracking.

### License
- MIT license.
- Copyright holder: `Andrej Berg`.
- Add `LICENSE` file to repo root before publishing.

### README additions
- Add a short pitch (2-3 sentences) before the Requirements section: what it does, why it exists (no block duplication, lean output), what MCP clients it targets.
- Add a tool table listing all 9 tools with one-line descriptions. Positioned after the pitch, before Requirements.
- No badges, no demo screenshots — keep it slim.

### GitHub repository metadata
- Description: `Python MCP server for Logseq`
- Topics: `mcp`, `logseq`, `python`
- Account: personal (`andrej-berg`) — already matches pyproject.toml URLs.
- Visibility: public from initial push.

### Claude's Discretion
- Exact wording of the 2-3 sentence pitch.
- Tool table format (markdown table vs. bullet list).
- Placement of the tool table within the README.

</decisions>

<specifics>
## Specific Ideas

- No rewrite of git history needed — first public push is sufficient since the repo has no remote yet.
- pyproject.toml already has correct GitHub URLs (`Homepage`, `Repository`) — no changes needed there.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `README.md`: already has Requirements, Install, Run Locally, MCP Client Config, and Troubleshooting sections. Additions slot in before Requirements.
- `.gitignore`: already ignores `graphthulhu/`, `logseq_docs/`, `.claude/`. Three new entries needed: `.planning/`, `logseq-test-graph/`, `CLAUDE.md`.
- `pyproject.toml`: `name`, `description`, `authors`, and `[project.urls]` already point to `andrej-berg/ya-logseq-mcp` — no changes needed.

### Established Patterns
- README-first documentation policy (Phase 8, 10): README is the single user-facing source of truth.
- Slim docs preference: no extra files, no badges, no separate CONTRIBUTING.md for this release.

### Integration Points
- `.gitignore` update → untrack `.planning/`, `logseq-test-graph/`, `CLAUDE.md` with `git rm -r --cached`.
- `LICENSE` file added to repo root.
- `README.md` pitch + tool table added.
- GitHub repo created via `gh repo create` and initial push.

</code_context>

<deferred>
## Deferred Ideas

- CONTRIBUTING.md — not needed for this release; GitHub Issues is sufficient for now.
- `claude` topic on GitHub — skipped; `mcp`, `logseq`, `python` are sufficient for discoverability.

</deferred>

---

*Phase: 11-github-publication-surface*
*Context gathered: 2026-03-16*
