# Requirements: ya-logseq-mcp

**Defined:** 2026-03-13
**Core Value:** Every read returns correctly structured blocks and every write produces valid Logseq content - no duplicates, no ghost blocks, no broken hierarchy.

## v1 Requirements

Requirements for milestone v1.2 (packaging and GitHub release).

### Branding and Naming

- [ ] **BRAND-01**: Maintainer can set `ya-logseq-mcp` as the canonical name across package metadata, repository metadata, and documentation.
- [ ] **BRAND-02**: User can identify the same project name consistently across README, module/CLI entrypoints, and repository branding.

### Relocation and Configuration

- [ ] **MOVE-01**: Maintainer can relocate the repository to `~/Workspace/tools/ya-logseq-mcp` without breaking local development commands.
- [ ] **MOVE-02**: Maintainer can run existing scripts/tests after relocation with updated path assumptions and no stale references to the old location.
- [ ] **MOVE-03**: User can configure clients using updated examples that reference the new project name and location.

### Documentation and Installation UX

- [ ] **DOCS-01**: User can follow installation instructions from a clean environment without hidden prerequisites.
- [ ] **DOCS-02**: User can configure the MCP server in Claude Desktop (or equivalent MCP clients) using copy-paste-ready examples.
- [ ] **DOCS-03**: User can verify a successful installation through a documented smoke-check flow.

### Publishing

- [ ] **PUB-01**: Maintainer can create and push a public GitHub repository for `ya-logseq-mcp` with complete repository metadata.
- [ ] **PUB-02**: User can discover setup, usage, and troubleshooting information directly from the GitHub repository home.

## v2 Requirements

Deferred to future milestones.

### Query and Template Tools

- **QUERY-01**: User can run raw DataScript queries with explicit error handling (`query`).
- **QUERY-02**: User can find blocks/pages by tag with input sanitization (`find_by_tag`).
- **QUERY-03**: User can find blocks/pages by property key/value with input sanitization (`query_properties`).
- **TMPL-01**: User can list templates (`template_list`).
- **TMPL-02**: User can fetch a template by name (`template_get`).
- **TMPL-03**: User can create templates from existing blocks (`template_create`).
- **TMPL-04**: User can delete templates (`template_delete`).
- **TMPL-05**: User can apply templates to a page or block (`template_apply`).

## Out of Scope

| Feature | Reason |
|---------|--------|
| New MCP tool surface in v1.2 | This milestone is release hardening and publication for existing functionality. |
| Deep feature expansion beyond publish readiness | Focus is relocation, naming, docs quality, and GitHub release. |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| BRAND-01 | Phase TBD | Pending |
| BRAND-02 | Phase TBD | Pending |
| MOVE-01 | Phase TBD | Pending |
| MOVE-02 | Phase TBD | Pending |
| MOVE-03 | Phase TBD | Pending |
| DOCS-01 | Phase TBD | Pending |
| DOCS-02 | Phase TBD | Pending |
| DOCS-03 | Phase TBD | Pending |
| PUB-01 | Phase TBD | Pending |
| PUB-02 | Phase TBD | Pending |

**Coverage:**
- v1 requirements: 10 total
- Mapped to phases: 0
- Unmapped: 10 ⚠️

---
*Requirements defined: 2026-03-13*
*Last updated: 2026-03-13 after v1.2 milestone requirement scoping*
