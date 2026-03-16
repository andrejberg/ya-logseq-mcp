# ya-logseq-mcp

Python MCP server for Logseq.

## What This Is

`ya-logseq-mcp` exposes Logseq read/write tools over MCP stdio so MCP clients can automate page and block workflows.

## Requirements

- Python 3.12+
- `uv`
- Logseq Desktop running with HTTP API enabled
- `LOGSEQ_API_TOKEN` from Logseq

## Install

```bash
uv sync
```

## Run Locally

```bash
LOGSEQ_API_TOKEN=<token> uv run --project ~/Workspace/tools/ya-logseq-mcp ya-logseq-mcp
```

Module fallback for troubleshooting:

```bash
LOGSEQ_API_TOKEN=<token> uv run --project ~/Workspace/tools/ya-logseq-mcp python -m logseq_mcp
```

## MCP Client Config

Use the script entrypoint name and pin the project path with `--project`:

```json
{
  "mcpServers": {
    "ya-logseq-mcp": {
      "command": "uv",
      "args": [
        "run",
        "--project",
        "~/Workspace/tools/ya-logseq-mcp",
        "ya-logseq-mcp"
      ],
      "cwd": "~/Workspace/tools/ya-logseq-mcp",
      "env": {
        "LOGSEQ_API_URL": "http://127.0.0.1:12315",
        "LOGSEQ_API_TOKEN": "<token>"
      }
    }
  }
}
```

## Smoke Check

```bash
uv run pytest tests/test_server.py -q
```

For maintainers, branding consistency checks are documented in `RUNBOOK.md`.

## Migration Note

This project was previously referred to as `logseq-mcp`; all current commands and config keys should use `ya-logseq-mcp`.
