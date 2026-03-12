# logseq-mcp Runbook

Operational knowledge for running, deploying, and troubleshooting the logseq-mcp server.

---

## MCP Config: `uv run` requires `--project`, not `cwd`

**Context:** Claude Code reads `.mcp.json` to start MCP servers. The `cwd` field in `.mcp.json` is **not reliably used** when spawning the server process — Claude Code may run the command from its own working directory instead.

**Symptom:** `logseq-mcp` shows as "not connected" when starting Claude from `~/Workspace/`, but works when starting from `~/Workspace/projects/logseq-mcp/`.

**Root cause:** `uv run python -m logseq_mcp` with `cwd` ignored means `uv` runs from `~/Workspace/`, finds no `pyproject.toml` there, falls back to `/usr/bin/python3`, and fails with `No module named logseq_mcp`.

**Fix:** Use `uv run --project <absolute-path>` to pin the project explicitly:

```json
{
  "mcpServers": {
    "logseq-mcp": {
      "command": "uv",
      "args": ["run", "--project", "/home/berga/Workspace/projects/logseq-mcp", "python", "-m", "logseq_mcp"],
      "env": { ... }
    }
  }
}
```

**Rule for shipping:** Always use `--project <absolute-path>` in any installation instructions or distributed `.mcp.json` examples. Never rely on `cwd`. Users installing the server from any working directory must have this flag set.

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `LOGSEQ_API_TOKEN` | yes | — | Auth token from Logseq settings |
| `LOGSEQ_API_URL` | no | `http://127.0.0.1:12315` | Logseq HTTP API endpoint |

---

## Starting the Server Manually

```bash
LOGSEQ_API_TOKEN=<token> uv run --project /path/to/logseq-mcp python -m logseq_mcp
```

Server speaks MCP over stdio — it will block waiting for input. Use Claude Code or another MCP client to connect.

---

## Smoke Test

With Logseq running and API enabled:

```bash
source ~/Workspace/.env
uv run --project /home/berga/Workspace/projects/logseq-mcp pytest tests/ -x
```
