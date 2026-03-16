# ya-logseq-mcp

Python MCP server for Logseq.

## What This Is

`ya-logseq-mcp` exposes Logseq read/write tools over MCP stdio so MCP clients can automate page and block workflows.

## Requirements

Complete this checklist before install:

- [ ] Python 3.12+ is installed: `python3 --version`
- [ ] `uv` is installed: `uv --version`
- [ ] Logseq Desktop is running with API enabled:
  `Settings -> Features -> Enable developer mode -> Enable API server`
- [ ] `LOGSEQ_API_TOKEN` is available from Logseq:
  `Settings -> Features -> API server -> API token`

## Install

Run from a fresh shell:

```bash
set -euo pipefail
cd ~/Workspace/tools/ya-logseq-mcp
python3 --version
uv --version
uv sync
```

## Run Locally

Script-first launch:

```bash
LOGSEQ_API_TOKEN=<token> uv run --project ~/Workspace/tools/ya-logseq-mcp ya-logseq-mcp
```

Module fallback for troubleshooting only:

```bash
LOGSEQ_API_TOKEN=<token> uv run --project ~/Workspace/tools/ya-logseq-mcp python -m logseq_mcp
```

expected first-run result:

- Process starts without Python traceback.
- MCP server stays attached to stdio while the client is connected.
- `health` requests return `{"status":"ok",...}` from your MCP client.

## MCP Client Config

Primary example for Claude Desktop (copy/paste-ready):

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

equivalent MCP clients (Cursor, VS Code MCP, custom launchers) should use the same
`command`, `args`, `cwd`, and `env` shape.
startup semantics: `command` + `args` must launch the `ya-logseq-mcp` entrypoint.
parse validation for this JSON block is included in the verification commands for this plan.

## Smoke Check

Run checks in this order:

1. Unit smoke:

```bash
uv run --project ~/Workspace/tools/ya-logseq-mcp pytest tests/test_server.py -q
```

2. MCP stdio integration smoke:

```bash
source ~/Workspace/.env
uv run --project ~/Workspace/tools/ya-logseq-mcp pytest tests/integration/test_mcp_stdio.py -x -q -m integration
```

Pass/fail interpretation:

- PASS: pytest exits `0` and reports passing tests.
- FAIL: pytest exits non-zero or reports failures/errors.

If smoke fails:

1. Re-check token and API availability (`LOGSEQ_API_TOKEN`, Logseq API enabled).
2. Re-run locally with `uv run --project ~/Workspace/tools/ya-logseq-mcp ya-logseq-mcp --help`.
3. Follow troubleshooting and maintainer checks in `RUNBOOK.md`.

## Docs-Only Onboarding Verification (fresh shell)

Use this when validating docs from a clean environment:

```bash
env -i HOME="$HOME" PATH="$PATH" bash -lc '
  set -euo pipefail
  cd ~/Workspace/tools/ya-logseq-mcp
  python3 --version
  uv --version
  uv sync
  test -n "${LOGSEQ_API_TOKEN:-}" || echo "LOGSEQ_API_TOKEN not set in fresh shell"
  uv run --project ~/Workspace/tools/ya-logseq-mcp ya-logseq-mcp --help >/tmp/phase10_docs_help.txt
'
```

DOCS-01 success markers:

- prereqs visible in output (`python --version`, `uv --version`)
- install command succeeds (`uv sync`)
- startup command reaches ready/no-traceback state (`ya-logseq-mcp --help` exits cleanly)

For maintainers, onboarding accuracy checks live in `RUNBOOK.md`.

## Migration Note

This project was previously referred to as `logseq-mcp`; all current commands and config keys should use `ya-logseq-mcp`.
