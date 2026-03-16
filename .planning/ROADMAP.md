# Roadmap: ya-logseq-mcp

## Milestones

- ✅ **v1.0 Logseq MCP Server MVP** - Phases 1-4 shipped on 2026-03-12
- ✅ **v1.1 Journals and Lifecycle Tools** - Phases 5-7 shipped on 2026-03-13
- 📋 **v1.2 Packaging and GitHub Release** - Phases 8-11 planned

## Phases

<details>
<summary>✅ v1.0 Logseq MCP Server MVP (Phases 1-4) - SHIPPED 2026-03-12</summary>

See `.planning/milestones/v1.0-ROADMAP.md` for the archived milestone roadmap.

</details>

<details>
<summary>✅ v1.1 Journals and Lifecycle Tools (Phases 5-7) - SHIPPED 2026-03-13</summary>

See `.planning/milestones/v1.1-ROADMAP.md` for the archived milestone roadmap.

</details>

### 📋 v1.2 Packaging and GitHub Release (Planned)

**Milestone Goal:** Ship the current MCP server as `ya-logseq-mcp` with coherent naming, relocation, onboarding docs, and GitHub publication.

- [x] **Phase 8: Branding Alignment** - Canonical `ya-logseq-mcp` naming is consistent across package/repo/docs and user-facing entrypoints. (completed 2026-03-13)
- [x] **Phase 9: Relocation and Runtime Configuration** - Repository move and path assumptions are updated with working dev/test workflows and client config examples. (completed 2026-03-16)
- [x] **Phase 10: Installation and Onboarding UX** - Setup documentation is end-to-end runnable from a clean environment with explicit smoke checks. (completed 2026-03-16)
- [ ] **Phase 11: GitHub Publication Surface** - Public repository publishing and GitHub-home discoverability are complete.

## Phase Details

### Phase 8: Branding Alignment
**Goal**: Maintainers and users see one canonical project identity (`ya-logseq-mcp`) across metadata, docs, and runtime touchpoints.
**Depends on**: Phase 7
**Requirements**: BRAND-01, BRAND-02
**Success Criteria** (what must be TRUE):
  1. Maintainer can set and verify `ya-logseq-mcp` as the canonical name in package metadata, repository metadata, and core documentation.
  2. User sees the same project name across README, module/CLI entrypoints, and repository branding without conflicting aliases.
  3. User can copy usage examples without encountering old project naming.
**Plans**: 2/2 complete (10-01, 10-02)

### Phase 9: Relocation and Runtime Configuration
**Goal**: The project runs from `~/Workspace/tools/ya-logseq-mcp` with updated path assumptions and client configuration examples.
**Depends on**: Phase 8
**Requirements**: MOVE-01, MOVE-02, MOVE-03
**Success Criteria** (what must be TRUE):
  1. Maintainer can relocate the repository to `~/Workspace/tools/ya-logseq-mcp` and still run development commands successfully.
  2. Maintainer can run existing scripts/tests after relocation with no stale references to `~/Workspace/projects/logseq-mcp`.
  3. User can configure MCP clients using examples that point to the new project name and location.
**Plans**: 2/2 complete (09-01, 09-02)

### Phase 10: Installation and Onboarding UX
**Goal**: New users can install, configure, and validate the MCP server from docs alone.
**Depends on**: Phase 9
**Requirements**: DOCS-01, DOCS-02, DOCS-03
**Success Criteria** (what must be TRUE):
  1. User can complete installation from a clean environment using documented prerequisites and commands only.
  2. User can configure Claude Desktop (or equivalent MCP clients) via copy-paste-ready configuration examples.
  3. User can run a documented smoke-check flow and confirm the installation is working.
**Plans**: TBD

### Phase 11: GitHub Publication Surface
**Goal**: The renamed project is publicly published on GitHub with enough guidance to onboard from the repository homepage.
**Depends on**: Phase 10
**Requirements**: PUB-01, PUB-02
**Success Criteria** (what must be TRUE):
  1. Maintainer can create and push a public GitHub repository for `ya-logseq-mcp` with complete repository metadata.
  2. User landing on the GitHub repository can find setup, usage, and troubleshooting guidance without external docs.
**Plans**: TBD

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Foundation | v1.0 | 3/3 | Complete | 2026-03-12 |
| 2. Core Reads | v1.0 | 3/3 | Complete | 2026-03-12 |
| 3. Write Tools | v1.0 | 3/3 | Complete | 2026-03-12 |
| 4. Integration and Swap | v1.0 | 3/3 | Complete | 2026-03-12 |
| 5. Lifecycle Write Semantics | v1.1 | 2/2 | Complete | 2026-03-13 |
| 6. Block Moves and Journal Writes | v1.1 | 5/5 | Complete | 2026-03-13 |
| 7. Journal Range and Milestone Validation | v1.1 | 3/3 | Complete | 2026-03-13 |
| 8. Branding Alignment | v1.2 | 2/2 | Complete | 2026-03-13 |
| 9. Relocation and Runtime Configuration | v1.2 | 2/2 | Complete | 2026-03-16 |
| 10. Installation and Onboarding UX | v1.2 | 2/2 | Complete | 2026-03-16 |
| 11. GitHub Publication Surface | v1.2 | 0/TBD | Not started | - |
