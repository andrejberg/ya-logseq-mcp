# Codebase Structure

**Analysis Date:** 2026-03-09

## Directory Layout

```
logseq-mcp/
├── CLAUDE.md               # Project identity, design spec, tool catalog
├── pyproject.toml           # uv project config, deps, build system
├── .gitignore               # Python/uv/IDE ignores + reference dirs
├── src/
│   └── logseq_mcp/
│       ├── __init__.py      # Package init (placeholder)
│       ├── __main__.py      # Entry point: python -m logseq_mcp
│       ├── py.typed         # PEP 561 marker for type checking
│       ├── server.py        # [TO CREATE] MCP server + tool registration
│       ├── client.py        # [TO CREATE] Async Logseq HTTP client
│       ├── types.py         # [TO CREATE] Pydantic models
│       └── tools/
│           ├── __init__.py  # Tools package init
│           ├── core.py      # [TO CREATE] get_page, get_block, list_pages, etc.
│           ├── journal.py   # [TO CREATE] journal_today, journal_append, journal_range
│           ├── kanban.py    # [TO CREATE] kanban_get, kanban_move, etc.
│           ├── templates.py # [TO CREATE] template CRUD + apply
│           └── write.py     # [TO CREATE] page_create, block_append, etc.
├── tests/
│   └── __init__.py          # Tests package init
├── graphthulhu/             # [GITIGNORED] Reference Go implementation
│   ├── client/logseq.go     # API call patterns to replicate
│   ├── types/logseq.go      # Data models to replicate in Pydantic
│   ├── tools/               # Tool implementations to port
│   ├── backend/backend.go   # Interface contract (subset)
│   ├── server.go            # Tool registration pattern
│   └── ...
├── logseq_docs/             # [GITIGNORED] Logseq API documentation reference
├── .planning/
│   └── codebase/            # Architecture and analysis documents
└── .venv/                   # [GITIGNORED] uv virtual environment
```

## Directory Purposes

**`src/logseq_mcp/`:**
- Purpose: Main package -- all production source code
- Contains: Server, client, types, and tool modules
- Key files: `server.py` (server setup), `client.py` (API communication), `types.py` (data models)

**`src/logseq_mcp/tools/`:**
- Purpose: MCP tool implementations grouped by domain
- Contains: One module per tool domain (core reads, writes, journal, kanban, templates)
- Key files: `core.py` (most-used read tools), `write.py` (mutation tools)

**`tests/`:**
- Purpose: Test suite
- Contains: Test modules (currently empty scaffolding)
- Key files: `test_client.py` (planned -- client unit tests)

**`graphthulhu/`:**
- Purpose: Reference implementation (Go) -- read-only, not part of this project's git
- Contains: The original MCP server being replaced
- Generated: No
- Committed: No (gitignored)

**`logseq_docs/`:**
- Purpose: Logseq API documentation for reference
- Contains: Official Logseq docs pages
- Generated: No
- Committed: No (gitignored)

**`.planning/`:**
- Purpose: GSD planning and analysis documents
- Contains: Codebase mapping docs consumed by planning/execution agents
- Generated: By mapping agents
- Committed: Yes

## Key File Locations

**Entry Points:**
- `src/logseq_mcp/__main__.py`: CLI entry -- `python -m logseq_mcp` or `uv run logseq-mcp`
- `src/logseq_mcp/server.py`: MCP server creation and tool registration

**Configuration:**
- `pyproject.toml`: Dependencies, build system, script entry points
- `.gitignore`: Exclusion rules including reference dirs

**Core Logic:**
- `src/logseq_mcp/client.py`: Async HTTP client for Logseq API
- `src/logseq_mcp/types.py`: Pydantic models for pages, blocks, refs
- `src/logseq_mcp/tools/core.py`: Primary read tools (get_page, get_block, list_pages, query)
- `src/logseq_mcp/tools/write.py`: Mutation tools (create, update, delete)
- `src/logseq_mcp/tools/journal.py`: Journal-specific tools
- `src/logseq_mcp/tools/kanban.py`: Kanban board tools (workspace-specific)
- `src/logseq_mcp/tools/templates.py`: Template CRUD tools

**Testing:**
- `tests/test_client.py`: Client unit tests (planned)

**Reference (read-only, gitignored):**
- `graphthulhu/client/logseq.go`: API call patterns
- `graphthulhu/types/logseq.go`: Entity models
- `graphthulhu/tools/navigate.go`: Read tool logic
- `graphthulhu/tools/search.go`: DataScript query patterns
- `graphthulhu/tools/write.go`: Write tool logic
- `graphthulhu/tools/journal.go`: Journal date handling
- `graphthulhu/server.go`: Tool registration pattern
- `graphthulhu/backend/backend.go`: Backend interface

## Naming Conventions

**Files:**
- `snake_case.py` for all Python modules: `client.py`, `types.py`, `server.py`
- Tool modules named by domain: `core.py`, `journal.py`, `kanban.py`, `templates.py`, `write.py`
- Test files prefixed with `test_`: `test_client.py`

**Directories:**
- `snake_case` for Python packages: `logseq_mcp`, `tools`
- Lowercase for top-level dirs: `src`, `tests`

**Functions:**
- `snake_case` for all functions and methods
- Tool handler functions match MCP tool names: `get_page()`, `block_append()`, `kanban_move()`
- Client methods match Logseq API method names in snake_case: `get_page()`, `get_page_blocks_tree()`

**Classes:**
- `PascalCase`: `PageEntity`, `BlockEntity`, `LogseqClient`

**Constants:**
- `UPPER_SNAKE_CASE` for true constants: `DEFAULT_API_URL`
- Kanban columns: `BACKLOG`, `SPRINT BACKLOG`, `IN PROGRESS`, `FINISHED`

## Where to Add New Code

**New MCP Tool:**
1. Add handler function in the appropriate `src/logseq_mcp/tools/<domain>.py`
2. Register the tool in `src/logseq_mcp/server.py`
3. Add any new Pydantic models to `src/logseq_mcp/types.py`
4. Add tests in `tests/test_<domain>.py`

**New Tool Domain (e.g., a new group of related tools):**
1. Create `src/logseq_mcp/tools/<domain>.py`
2. Export handler functions
3. Import and register in `src/logseq_mcp/server.py`

**New Logseq API Method:**
1. Add typed method to `src/logseq_mcp/client.py`
2. Add response model to `src/logseq_mcp/types.py` if needed

**New Test:**
1. Create or extend `tests/test_<module>.py`
2. Use `pytest-asyncio` for async tests
3. Mock `httpx` responses (do not call live Logseq in unit tests)

**Utilities/Helpers:**
- Small helpers: keep in the module that uses them
- Shared helpers: add to the relevant layer file (`client.py` for HTTP helpers, `types.py` for model helpers)
- Do not create a generic `utils.py` -- keep helpers close to their consumers

## Special Directories

**`graphthulhu/`:**
- Purpose: Reference Go implementation (the server being replaced)
- Generated: No -- cloned repo
- Committed: No (gitignored)
- Note: Has its own `.git` directory. Read-only reference. Do not modify.

**`logseq_docs/`:**
- Purpose: Logseq API documentation
- Generated: No -- cloned repo
- Committed: No (gitignored)
- Note: Has its own `.git` directory. Read-only reference.

**`.venv/`:**
- Purpose: uv-managed Python virtual environment
- Generated: Yes (`uv sync`)
- Committed: No (gitignored)

**`.planning/`:**
- Purpose: GSD codebase analysis and planning documents
- Generated: By mapping/planning agents
- Committed: Yes

## Project Status

The project is in **early scaffold** phase. Only the directory structure and empty files exist:
- `pyproject.toml` is complete with deps declared
- `__init__.py` has a placeholder `hello()` function
- `__main__.py` is empty (0 bytes)
- `server.py`, `client.py`, `types.py` do not exist yet
- All `tools/*.py` files are empty `__init__.py` stubs
- `tests/` has only an empty `__init__.py`

Implementation follows the phased plan in `CLAUDE.md` (Foundation -> Core Reads -> Writes -> Journal -> Templates -> Kanban -> Integration).

---

*Structure analysis: 2026-03-09*
