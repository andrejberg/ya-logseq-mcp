# ya-logseq-mcp Runbook

Internal operational notes for maintainers.

User-facing install/run/config guidance lives in `README.md` and is canonical.

## Operational Constraints

- Always invoke `uv run` with `--project /absolute/path/to/repo` when launched by external tools.
- Keep MCP server key and script naming aligned to `ya-logseq-mcp`.
- Treat `README.md` as the only onboarding source; this runbook should not duplicate setup steps.

## Troubleshooting

### Server does not start from MCP client

- Symptom: client reports the server is disconnected.
- Check: command includes `--project` and points at this repository.
- Check: `LOGSEQ_API_TOKEN` is set and Logseq HTTP API is enabled.

### Quick maintainer smoke

```bash
source ~/Workspace/.env
uv run --project /home/berga/Workspace/projects/logseq-mcp pytest tests/test_server.py -q
```
