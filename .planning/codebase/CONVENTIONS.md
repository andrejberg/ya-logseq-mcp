# Coding Conventions

**Analysis Date:** 2026-03-09

## Status

This project is in **early scaffold stage** (Phase 1 not yet started). The conventions below are derived from `CLAUDE.md` design spec and `pyproject.toml` configuration. Follow these prescriptively when writing new code.

## Naming Patterns

**Files:**
- Use `snake_case.py` for all Python modules
- Tool modules grouped by domain: `core.py`, `journal.py`, `kanban.py`, `templates.py`, `write.py`
- One module per concern: `client.py` (HTTP), `types.py` (models), `server.py` (MCP registration)

**Functions:**
- Use `snake_case` for all functions and methods
- Tool handler names match the MCP tool name exactly: `get_page`, `block_append`, `kanban_move`
- All tool handlers must be `async def`

**Variables:**
- Use `snake_case` for variables and parameters
- Constants use `UPPER_SNAKE_CASE` (e.g., kanban columns: `BACKLOG`, `SPRINT BACKLOG`, `IN PROGRESS`, `FINISHED`)

**Types:**
- Use `PascalCase` for Pydantic models and classes
- Model names: `PageEntity`, `BlockEntity`, `PageRef`, `BlockRef`

## Code Style

**Formatting:**
- No formatter configured yet (ruff, black, etc. not in `pyproject.toml`)
- Recommendation: Add `ruff` as dev dependency for formatting and linting
- `py.typed` marker present at `src/logseq_mcp/py.typed` -- this is a typed package

**Linting:**
- No linter configured yet
- Recommendation: Add `ruff` with standard rules to `pyproject.toml` `[tool.ruff]`

**Type Hints:**
- Use type hints on all function signatures
- Return type annotations required (the `-> str` pattern is used in `src/logseq_mcp/__init__.py`)
- Pydantic v2 models for all data structures (`pydantic>=2.0.0`)

## Python Version

- Requires Python >= 3.12 (declared in `pyproject.toml`)
- Use modern Python features: `type` aliases, `|` union syntax, `match` statements where appropriate

## Import Organization

**Order:**
1. Standard library imports
2. Third-party imports (`httpx`, `pydantic`, `mcp`)
3. Local imports (`logseq_mcp.*`)

**Path Aliases:**
- No path aliases -- use relative or absolute imports within the `logseq_mcp` package
- Entry point: `logseq_mcp.__main__:main`

## Async Patterns

**All tool handlers are async:**
```python
async def get_page(name: str, lean: bool = True) -> dict:
    ...
```

**HTTP client:**
- Use `httpx.AsyncClient` exclusively (not `requests`, not sync `httpx`)
- Client lives in `src/logseq_mcp/client.py`
- Implement retry logic in the client layer

## Error Handling

**Patterns:**
- Handle HTTP errors in `client.py` -- tool modules should not deal with raw HTTP
- Use Pydantic validation for input/output data shapes
- Logseq API errors should be caught and wrapped with meaningful messages

**Expected error types:**
- Connection errors (Logseq not running)
- Auth errors (bad/missing token)
- Not-found errors (page/block does not exist)
- DataScript query errors (malformed query)

## Logging

**Framework:** Not yet configured
- Recommendation: Use Python `logging` module with structured output
- Log at `DEBUG` level for API calls, `INFO` for tool invocations, `ERROR` for failures

## Comments

**When to Comment:**
- DataScript queries should have inline comments explaining the query logic
- Complex deduplication logic (e.g., UUID-based dedup in `get_page`) should be commented
- Do not comment obvious code

**Docstrings:**
- All public functions and tool handlers should have docstrings
- Docstrings become MCP tool descriptions -- keep them concise and user-facing

## Module Design

**Exports:**
- `__init__.py` files should be minimal (empty or re-exports only)
- `src/logseq_mcp/tools/__init__.py` should export tool registration functions

**Barrel Files:**
- `tools/__init__.py` serves as the barrel for all tool modules

## Pydantic Model Patterns

**Models in `src/logseq_mcp/types.py`:**
- Mirror graphthulhu's `types/logseq.go` data model
- Use Pydantic validators for flexible input (e.g., `PageRef` handles both `{"id": N}` and plain `N`)
- All fields optional where the Logseq API may omit them
- Use `model_config` for JSON serialization settings

## Configuration

**Environment variables:**
- `LOGSEQ_API_URL` -- defaults to `http://127.0.0.1:12315`
- `LOGSEQ_API_TOKEN` -- required, no default
- Read via `os.environ` or a Pydantic `BaseSettings` class

## MCP Tool Registration

**Pattern (from `CLAUDE.md` design):**
- Tools registered in `src/logseq_mcp/server.py`
- Each tool module in `src/logseq_mcp/tools/` contains handler functions
- Server imports and registers handlers from tool modules
- Tool names use `snake_case` matching the function name

## Kanban-Specific Conventions

**Column names are exact strings:**
- `BACKLOG`, `SPRINT BACKLOG`, `IN PROGRESS`, `FINISHED`

**Task properties follow workspace schema:**
```
type:: Task
project:: <slug>
task_type:: <dev|research|documentation|infra>
execution_type:: <automated|semi-automated|manual>
effort:: <1-13>
description:: <what>
dod:: <done criteria>
assignee::
```

## Journal Date Handling

**Try multiple formats in order:**
1. `"Mar 8th, 2026"`
2. `"March 8th, 2026"`
3. `"2026-03-08"`
4. `"March 8, 2026"`

---

*Convention analysis: 2026-03-09*
