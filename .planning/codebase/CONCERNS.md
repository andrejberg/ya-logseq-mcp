# Codebase Concerns

**Analysis Date:** 2026-03-09

## Tech Debt

**Scaffold-only implementation:**
- Issue: The project is scaffolded but contains no actual implementation. All source files are empty stubs: `src/logseq_mcp/__init__.py` has a placeholder `hello()` function, `src/logseq_mcp/__main__.py` is empty, `src/logseq_mcp/tools/__init__.py` is empty. The planned files `server.py`, `client.py`, `types.py`, and all tool modules (`core.py`, `journal.py`, `kanban.py`, `templates.py`, `write.py`) do not exist yet.
- Files: `src/logseq_mcp/__init__.py`, `src/logseq_mcp/__main__.py`, `src/logseq_mcp/tools/__init__.py`
- Impact: No functionality exists. The entire 27-tool surface area defined in `CLAUDE.md` must be implemented from scratch.
- Fix approach: Follow the 7-phase implementation plan in `CLAUDE.md`. Phase 1 (Foundation) is partially complete (pyproject.toml exists with correct deps, directory structure created).

**No template API precedent in graphthulhu:**
- Issue: The planned template tools (`template_list`, `template_get`, `template_create`, `template_delete`, `template_apply`) reference Logseq `App.*` API methods (`getCurrentGraphTemplates`, `getTemplate`, `createTemplate`, `removeTemplate`, `insertTemplate`) that graphthulhu never implemented. There is zero reference code for these 5 tools.
- Files: `CLAUDE.md` (tool spec section)
- Impact: Template tools cannot be copy-adapted from graphthulhu. The Logseq `App.*` template API methods are undocumented in the reference materials and may not exist or may have different signatures than assumed. Implementation will require live API experimentation.
- Fix approach: During Phase 5, probe each `App.*` method against a live Logseq instance to verify existence and signatures before implementing. Have a fallback plan: templates in Logseq are blocks with `template::` property, so DataScript queries can serve as an alternative discovery mechanism.

**No kanban precedent in graphthulhu:**
- Issue: The 4 planned kanban tools (`kanban_get`, `kanban_move`, `kanban_add_task`, `kanban_list`) are entirely new. They encode workspace-specific conventions (4 column names: BACKLOG, SPRINT BACKLOG, IN PROGRESS, FINISHED) and a task property schema (`type::`, `project::`, `effort::`, `dod::`, etc.).
- Files: `CLAUDE.md` (kanban section)
- Impact: These tools are workspace-coupled, not generic. If the Kanban column naming convention changes in the Logseq graph, these tools break silently. The task property schema is hardcoded rather than configurable.
- Fix approach: Make column names and required task properties configurable (env vars or a config dict), not hardcoded constants. Document the coupling explicitly in tool descriptions.

## Known Bugs

**graphthulhu block duplication bug (the reason this project exists):**
- Symptoms: `get_page` returns blocks 4-8x duplicated due to recursive traversal in `enrichBlockTree` combined with how Logseq's `getPageBlocksTree` returns children both inline and as top-level entries.
- Files: `graphthulhu/tools/navigate.go` (lines 443-460, `enrichBlockTree` function)
- Trigger: Call `get_page` on any page with nested blocks. The enrichment re-walks children that are already present in the tree.
- Workaround: The new implementation must deduplicate by UUID at read time. Use a `seen: set[str]` during tree traversal in the Python `get_page` implementation.

**graphthulhu DataScript injection in query_properties and find_by_tag:**
- Symptoms: User-supplied property names and values are interpolated directly into DataScript query strings via `fmt.Sprintf` without sanitization.
- Files: `graphthulhu/tools/search.go` (lines 159-169), `graphthulhu/tools/navigate.go` (lines 206-209, 337-340)
- Trigger: Pass a property value containing `"]` or Clojure escape sequences.
- Workaround: In the Python implementation, sanitize all user inputs before interpolating into DataScript queries. Strip or escape `]`, `"`, and backslash characters. Consider using DataScript parameterized inputs where the API supports them (`logseq.DB.datascriptQuery` accepts additional input arguments after the query string).

## Security Considerations

**DataScript query injection:**
- Risk: The `query` tool exposes raw DataScript passthrough. While this is intentional (power-user feature), combined with `query_properties` and `find_by_tag` which build queries from user input, there is no input validation layer.
- Files: Planned `src/logseq_mcp/tools/core.py` (not yet implemented)
- Current mitigation: None in graphthulhu. The Logseq API itself provides some protection since DataScript queries are read-only at the DB level, but malformed queries could cause crashes or hangs.
- Recommendations: For `query_properties` and `find_by_tag`, validate/sanitize property names (alphanumeric + hyphens only) and values (escape double quotes). For `query` (raw passthrough), document that it accepts arbitrary DataScript and leave validation to the caller (LLM).

**API token handling:**
- Risk: `LOGSEQ_API_TOKEN` is read from environment. The token grants full read/write access to the Logseq graph including page deletion.
- Files: Planned `src/logseq_mcp/client.py`
- Current mitigation: `.env` is in `.gitignore`. Token is not hardcoded anywhere.
- Recommendations: Validate that the token is present at startup and fail fast with a clear error message rather than silently operating without auth. Consider adding a read-only mode flag (as graphthulhu does) to limit write operations.

**Write operations have no confirmation or undo:**
- Risk: `delete_page`, `block_delete`, and `rename_page` are destructive and irreversible through the API. An LLM calling these tools could accidentally destroy data.
- Files: Planned `src/logseq_mcp/tools/write.py`
- Current mitigation: The Logseq graph is git-tracked, so changes can be reverted at the filesystem level.
- Recommendations: Add explicit `"destructive": true` metadata to delete/rename tool descriptions so LLMs treat them with appropriate caution. Consider a dry-run mode for destructive operations.

## Performance Bottlenecks

**ListPages with tag filter scans all pages:**
- Problem: In graphthulhu, `list_pages` with `hasTag` filter calls `GetPageBlocksTree` for every page in the graph to check for tags. This is O(N) API calls where N is total page count.
- Files: `graphthulhu/tools/navigate.go` (lines 138-146)
- Cause: The Logseq API has no native "list pages by tag" endpoint. Each page's block tree must be fetched and scanned.
- Improvement path: In the Python implementation, use a DataScript query instead: `[:find (pull ?p [:block/name]) :where [?b :block/page ?p] [?b :block/refs ?ref] [?ref :block/name "tag-name"]]`. This is a single API call vs N calls. The graphthulhu `find_by_tag` already does this for blocks; extend the pattern for pages.

**Journal date format guessing requires up to 4 API calls per day:**
- Problem: `journal_range` tries 4 different page name formats per date (`"Mar 8th, 2026"`, `"March 8th, 2026"`, `"2026-03-08"`, `"March 8, 2026"`). For a 30-day range, this is up to 120 API calls.
- Files: `graphthulhu/tools/journal.go` (lines 44-58, 90-99)
- Cause: Logseq's journal page naming format is user-configurable and the API doesn't expose the configured format.
- Improvement path: On first successful journal lookup, cache the format that worked and try it first for subsequent dates. Alternatively, use DataScript to query by `journal-day` integer (YYYYMMDD format) which bypasses page name guessing entirely: `[:find (pull ?p [*]) :where [?p :block/journal? true] [?p :block/journal-day ?d] [(>= ?d 20260301)] [(<= ?d 20260331)]]`.

**GetAllPages called by multiple tools without caching:**
- Problem: `list_pages`, `health`, and graph analysis tools all call `getAllPages`. In a session with multiple tool calls, this same expensive operation repeats.
- Files: Planned `src/logseq_mcp/client.py`
- Cause: No request-level or session-level caching in the client.
- Improvement path: Add optional TTL-based caching to the client for read-only endpoints. Even a 5-second cache would eliminate redundant calls within a single LLM turn.

## Fragile Areas

**Logseq API response format assumptions:**
- Files: `graphthulhu/types/logseq.go` (full file), planned `src/logseq_mcp/types.py`
- Why fragile: The Pydantic models must match Logseq's actual JSON response format exactly. Logseq's API is not formally documented and response shapes have changed between versions. Key fragilities:
  - `BlockEntity.Children` can be full objects OR compact `[["uuid", "value"]]` arrays depending on the API method called (graphthulhu handles this with custom `UnmarshalJSON` at line 48-73 of `types/logseq.go`)
  - `PageRef` and `BlockRef` can be `{"id": N}` objects OR plain integers depending on context
  - `getPageLinkedReferences` returns `[[PageEntity, [BlockEntity, ...]], ...]` — a nested array-of-arrays, not a typed object
- Safe modification: Always test against a live Logseq instance after changing type definitions. Add defensive parsing (try/except with fallbacks) for every API response.
- Test coverage: No automated tests exist. The only test file `tests/__init__.py` is empty.

**DataScript query string construction:**
- Files: `graphthulhu/tools/search.go` (lines 157-169, 223-226), `graphthulhu/tools/navigate.go` (lines 206-209)
- Why fragile: Queries are built with string interpolation. A changed property name format, a tag with special characters, or a UUID in unexpected format will silently produce wrong results or errors.
- Safe modification: Build a small query builder utility that handles escaping and parameterization. Test with edge cases: property names with hyphens, tag names with spaces, UUIDs with non-standard formatting.
- Test coverage: Zero tests for query construction in graphthulhu.

**Logseq HTTP API availability:**
- Files: Planned `src/logseq_mcp/client.py`
- Why fragile: The MCP server depends on Logseq desktop app running with HTTP API enabled on port 12315. If Logseq is not running, all tools fail. There is no graceful degradation.
- Safe modification: Implement robust health checking at startup. Return clear error messages ("Logseq is not running or API is not enabled") rather than generic connection errors. Consider a startup probe that retries with backoff.
- Test coverage: No integration tests against live Logseq.

## Scaling Limits

**Logseq HTTP API is single-threaded:**
- Current capacity: One request at a time. Logseq processes API requests on its main thread.
- Limit: Concurrent async requests from the Python client will queue at the Logseq side. Sending many parallel requests (e.g., batch operations) could cause timeouts or UI freezes in Logseq.
- Scaling path: Implement request serialization in the Python client (asyncio semaphore with concurrency=1 or a request queue). Use batch operations (`insertBatchBlock`) where available instead of multiple single-block inserts.

## Dependencies at Risk

**`mcp>=1.0.0` — MCP SDK version range is too broad:**
- Risk: The `mcp` package is evolving rapidly. A major version bump could break the server registration API.
- Impact: Server startup failure after `uv sync` pulls a breaking update.
- Migration plan: Pin to a specific minor version range (e.g., `mcp>=1.0.0,<2.0.0`) once the implementation starts. Lock file (`uv.lock`) is present and provides reproducibility, but the constraint should still be tightened.

**Logseq HTTP API stability:**
- Risk: The Logseq HTTP API (`/api` endpoint) is an internal/plugin API, not a stable public API. Logseq DB version (tracked in `logseq_docs/db-version.md`) changes could alter response formats.
- Impact: Type deserialization failures, missing fields, changed method names.
- Migration plan: Monitor Logseq releases for API changes. The `logseq_docs/` reference directory is included in the project for this purpose. Add version detection to the `health` tool output.

## Missing Critical Features

**No test infrastructure:**
- Problem: `tests/__init__.py` is empty. No test runner configuration (`pytest.ini`, `pyproject.toml [tool.pytest]`), no fixtures, no mocks for the Logseq API.
- Blocks: Cannot verify any implementation correctness without manual testing against a live Logseq instance.
- Fix approach: Create mock fixtures for Logseq API responses (capture real responses and replay them). Add `[tool.pytest.ini_options]` to `pyproject.toml`. Build a `FakeLogseqClient` that returns canned responses for unit testing tool logic independently of the API.

**No error handling strategy defined:**
- Problem: The CLAUDE.md design spec does not define how errors should be reported to the MCP client. graphthulhu uses `errorResult()` which returns `IsError: true` with a text message, but the Python MCP SDK may have different conventions.
- Blocks: Inconsistent error handling across 27 tools if each implementer makes ad-hoc choices.
- Fix approach: Define error handling in Phase 1: create a helper function (like graphthulhu's `errorResult`) and use it consistently. Categorize errors: connection errors (Logseq not running), not-found errors (page/block doesn't exist), validation errors (bad input), and API errors (unexpected response).

**No logging:**
- Problem: Neither graphthulhu nor the planned implementation includes structured logging. When tools fail in production (inside an MCP session), there is no way to diagnose what happened.
- Blocks: Debugging issues requires reproducing them manually.
- Fix approach: Add Python `logging` with configurable level via `LOGSEQ_MCP_LOG_LEVEL` env var. Log all API calls at DEBUG level, errors at ERROR level. Use `stderr` for log output (MCP uses `stdout` for protocol communication).

## Test Coverage Gaps

**Entire codebase is untested:**
- What's not tested: Everything. Zero implementation exists, and the test directory contains only an empty `__init__.py`.
- Files: `tests/__init__.py`
- Risk: All 27 tools, the HTTP client, type parsing, DataScript query construction, journal date formatting, UUID deduplication logic — none of these will have automated verification.
- Priority: High. At minimum, the following need unit tests before the implementation can be trusted:
  1. UUID deduplication in `get_page` (the core bug fix motivating this project)
  2. Pydantic model parsing for `BlockEntity` and `PageEntity` with edge cases (compact refs, missing fields)
  3. DataScript query construction with special characters
  4. Journal date format generation and ordinal suffixes
  5. Kanban column name matching

---

*Concerns audit: 2026-03-09*
