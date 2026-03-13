# Phase 08 Branding Verification

Date: 2026-03-13
Plan: 08-02

## Scope

This record captures branding consistency checks for:

- package/repository metadata: `pyproject.toml` (`[project]`, `[project.urls]`, scripts)
- runtime touchpoints: `src/logseq_mcp/server.py`, `src/logseq_mcp/__init__.py`
- canonical docs surfaces: `README.md`, `RUNBOOK.md`
- controlled legacy-name allowance in docs

## Commands and Outputs

### 1) Test sanity

Command:

```bash
uv run pytest tests/test_server.py -q
```

Output:

```text
......                                                                   [100%]
6 passed in 0.29s
```

### 2) Canonical branding presence + repository metadata surface

Command:

```bash
rg -n "ya-logseq-mcp|^\[project\.urls\]" pyproject.toml src/logseq_mcp/server.py src/logseq_mcp/__init__.py README.md RUNBOOK.md
```

Output:

```text
RUNBOOK.md:1:# ya-logseq-mcp Runbook
RUNBOOK.md:10:- Keep MCP server key and script naming aligned to `ya-logseq-mcp`.
RUNBOOK.md:25:uv run --project /home/berga/Workspace/projects/ya-logseq-mcp pytest tests/test_server.py -q
RUNBOOK.md:33:rg -n "ya-logseq-mcp|^\[project\.urls\]" pyproject.toml src/logseq_mcp/server.py src/logseq_mcp/__init__.py README.md RUNBOOK.md
RUNBOOK.md:36:Optional legacy detector (avoids false positives on canonical `ya-logseq-mcp`):
README.md:1:# ya-logseq-mcp
README.md:7:`ya-logseq-mcp` exposes Logseq read/write tools over MCP stdio so MCP clients can automate page and block workflows.
README.md:35:    "ya-logseq-mcp": {
README.md:40:        "/home/berga/Workspace/projects/ya-logseq-mcp",
README.md:41:        "ya-logseq-mcp"
README.md:62:This project was previously referred to as `logseq-mcp`; all current commands and config keys should use `ya-logseq-mcp`.
src/logseq_mcp/__init__.py:1:"""ya-logseq-mcp: Custom Python MCP server for Logseq."""
pyproject.toml:2:name = "ya-logseq-mcp"
pyproject.toml:4:description = "ya-logseq-mcp: Python MCP server for Logseq"
pyproject.toml:16:[project.urls]
pyproject.toml:17:Homepage = "https://github.com/andrej-berg/ya-logseq-mcp"
pyproject.toml:18:Repository = "https://github.com/andrej-berg/ya-logseq-mcp"
pyproject.toml:21:ya-logseq-mcp = "logseq_mcp.__main__:main"
src/logseq_mcp/server.py:22:mcp = FastMCP("ya-logseq-mcp", lifespan=lifespan)
```

### 3) False-positive-safe legacy detector (primary)

Command:

```bash
rg -n -P "(?<!ya-)logseq-mcp" README.md RUNBOOK.md pyproject.toml src/logseq_mcp/server.py src/logseq_mcp/__init__.py
```

Output:

```text
README.md:62:This project was previously referred to as `logseq-mcp`; all current commands and config keys should use `ya-logseq-mcp`.
```

### 4) Legacy detector fallback (for environments without `rg -P`)

Command:

```bash
rg -n "logseq-mcp" README.md RUNBOOK.md pyproject.toml src/logseq_mcp/server.py src/logseq_mcp/__init__.py | rg -v "ya-logseq-mcp"
```

Output:

```text
(no matches)
```

## Requirement Mapping

- `BRAND-01`: Verified canonical `ya-logseq-mcp` identity in package metadata (`[project]`, `[project.urls]`, scripts), runtime (`FastMCP` name, package docstring), and canonical docs (`README`, `RUNBOOK`).
- `BRAND-02`: Verified controlled legacy-name allowance with a false-positive-safe detector; only explicit migration note in `README.md` remains.
