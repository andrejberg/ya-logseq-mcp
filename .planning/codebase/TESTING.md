# Testing Patterns

**Analysis Date:** 2026-03-09

## Status

This project is in **early scaffold stage**. Test infrastructure is declared in `pyproject.toml` but no tests have been written yet. The patterns below are prescriptive guidance for writing tests.

## Test Framework

**Runner:**
- pytest >= 8.0.0
- Config: None yet (no `pytest.ini`, no `[tool.pytest]` in `pyproject.toml`)
- Recommendation: Add `[tool.pytest.ini_options]` to `pyproject.toml`

**Async Support:**
- pytest-asyncio >= 0.24.0
- Use `@pytest.mark.asyncio` for all async test functions
- Recommendation: Set `asyncio_mode = "auto"` in pytest config to avoid per-test decoration

**Assertion Library:**
- Built-in pytest assertions (no additional assertion library)

**Run Commands:**
```bash
uv run pytest                    # Run all tests
uv run pytest -x                 # Stop on first failure
uv run pytest --tb=short         # Short tracebacks
uv run pytest -v                 # Verbose output
uv run pytest --cov=logseq_mcp  # Coverage (requires pytest-cov, not yet in deps)
```

## Test File Organization

**Location:**
- Separate `tests/` directory at project root (not co-located)
- `tests/__init__.py` exists (empty)

**Naming:**
- Test files: `test_<module>.py` (e.g., `test_client.py` per CLAUDE.md layout)
- Test functions: `test_<behavior>` or `test_<method>_<scenario>`

**Planned Structure (from CLAUDE.md):**
```
tests/
├── __init__.py
└── test_client.py      # Tests for src/logseq_mcp/client.py
```

**Recommended expansion:**
```
tests/
├── __init__.py
├── conftest.py          # Shared fixtures
├── test_client.py       # HTTP client tests
├── test_types.py        # Pydantic model tests
├── test_server.py       # MCP server registration tests
└── tools/
    ├── __init__.py
    ├── test_core.py     # get_page, get_block, list_pages, etc.
    ├── test_journal.py  # journal_today, journal_append, journal_range
    ├── test_kanban.py   # kanban_get, kanban_move, etc.
    ├── test_templates.py # template CRUD tests
    └── test_write.py    # page_create, block_append, etc.
```

## Test Structure

**Suite Organization:**
```python
import pytest
from logseq_mcp.client import LogseqClient


class TestLogseqClient:
    """Tests for the async Logseq HTTP client."""

    @pytest.mark.asyncio
    async def test_call_api_success(self, mock_httpx):
        """Successful API call returns parsed JSON."""
        client = LogseqClient(url="http://localhost:12315", token="test-token")
        result = await client.call("logseq.Editor.getAllPages", [])
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_call_api_connection_error(self, mock_httpx):
        """Connection error raises meaningful exception."""
        ...
```

**Patterns:**
- Group related tests in classes named `Test<Component>`
- Use descriptive docstrings on test methods
- One assertion focus per test (may have multiple asserts supporting one logical check)

## Mocking

**Framework:** `unittest.mock` (stdlib) + `pytest` fixtures

**Patterns -- Mock the HTTP layer:**
```python
import pytest
from unittest.mock import AsyncMock, patch
import httpx


@pytest.fixture
def mock_httpx():
    """Mock httpx.AsyncClient.post for all Logseq API calls."""
    with patch("logseq_mcp.client.httpx.AsyncClient.post") as mock_post:
        mock_post.return_value = httpx.Response(
            200,
            json={"result": [...]},
        )
        yield mock_post
```

**What to Mock:**
- `httpx.AsyncClient.post` -- the single HTTP call point to Logseq API
- Never mock Pydantic models or validation -- test those with real data
- Never mock internal deduplication or transformation logic

**What NOT to Mock:**
- Pydantic model construction and validation (test with real/sample data)
- DataScript query string building (test the actual output strings)
- UUID deduplication in `get_page` (test with duplicated input data)

## Fixtures and Factories

**Test Data -- Logseq API response fixtures:**
```python
@pytest.fixture
def sample_page_response():
    """Raw Logseq API response for getPage."""
    return {
        "id": 123,
        "uuid": "abc-def-123",
        "name": "test page",
        "originalName": "Test Page",
        "journal?": False,
        "properties": {},
    }


@pytest.fixture
def sample_blocks_tree_response():
    """Raw Logseq API response for getPageBlocksTree with duplicates."""
    return [
        {"id": 1, "uuid": "block-1", "content": "First block", "children": []},
        {"id": 1, "uuid": "block-1", "content": "First block", "children": []},  # duplicate
        {"id": 2, "uuid": "block-2", "content": "Second block", "children": []},
    ]
```

**Location:**
- Shared fixtures in `tests/conftest.py`
- Module-specific fixtures in the test file itself

## Coverage

**Requirements:** None enforced yet

**Recommendation:**
- Add `pytest-cov` to dev dependencies
- Target 80%+ coverage on `client.py` and `types.py`
- Tool handlers: test happy path + error path for each tool

**View Coverage:**
```bash
uv run pytest --cov=logseq_mcp --cov-report=term-missing
```

## Test Types

**Unit Tests:**
- Primary test type for this project
- Test Pydantic models with sample API responses
- Test client methods with mocked HTTP
- Test tool handlers with mocked client
- Test deduplication logic with crafted duplicate data

**Integration Tests:**
- Test against a live Logseq instance (requires Logseq running with API enabled)
- Mark with `@pytest.mark.integration` and skip by default
- Useful during Phase 7 (migration validation) for parity checks

**E2E Tests:**
- Not planned -- MCP protocol testing is handled by the MCP SDK's own test utilities

## Common Patterns

**Async Testing:**
```python
@pytest.mark.asyncio
async def test_get_page_deduplicates_blocks():
    """get_page returns unique blocks by UUID."""
    # Arrange: mock client returns duplicated blocks
    # Act: call get_page
    # Assert: result contains no duplicate UUIDs
    ...
```

**Error Testing:**
```python
@pytest.mark.asyncio
async def test_client_raises_on_connection_error():
    """Client wraps httpx.ConnectError with a clear message."""
    with pytest.raises(ConnectionError, match="Cannot connect to Logseq"):
        ...
```

**Pydantic Model Testing:**
```python
def test_page_ref_accepts_dict_format():
    """PageRef handles {"id": N} format."""
    ref = PageRef.model_validate({"id": 42})
    assert ref.id == 42


def test_page_ref_accepts_plain_int():
    """PageRef handles plain integer format."""
    ref = PageRef.model_validate(42)
    assert ref.id == 42
```

**Parametrized Tests for Date Formats:**
```python
@pytest.mark.parametrize("date_str", [
    "Mar 8th, 2026",
    "March 8th, 2026",
    "2026-03-08",
    "March 8, 2026",
])
def test_parse_journal_date(date_str):
    """All supported date formats parse to the same date."""
    ...
```

## Dependencies (dev group)

From `pyproject.toml` `[dependency-groups]`:
```toml
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
]
```

**Missing but recommended:**
- `pytest-cov` -- coverage reporting
- `respx` -- alternative to manual httpx mocking (purpose-built for httpx)

---

*Testing analysis: 2026-03-09*
