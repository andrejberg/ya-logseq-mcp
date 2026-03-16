# ya-logseq-mcp Runbook

Internal operational notes for maintainers.

User-facing install/run/config guidance lives in `README.md` and is canonical.

## Operational Constraints

- Always invoke `uv run` with `--project ~/Workspace/tools/ya-logseq-mcp` when launched by external tools.
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
uv run --project ~/Workspace/tools/ya-logseq-mcp pytest tests/test_server.py -q
```

## Branding Consistency Check

Use this check before merging doc or metadata edits:

```bash
rg -n "ya-logseq-mcp|^\[project\.urls\]" pyproject.toml src/logseq_mcp/server.py src/logseq_mcp/__init__.py README.md RUNBOOK.md
```

Optional legacy detector (avoids false positives on canonical `ya-logseq-mcp`):

```bash
rg -n -P '(?<!ya-)logseq[-]mcp' README.md RUNBOOK.md pyproject.toml src/logseq_mcp/server.py src/logseq_mcp/__init__.py
```

## Relocation Stale-Reference Scan

Use this before merges that touch docs, scripts, tests, or runtime configuration:

```bash
LEGACY_PATH_RE="projects/logseq""-mcp|/home/.*/Workspace/projects/logseq""-mcp|/home/.*/Workspace/projects/ya-logseq""-mcp"
rg -n "$LEGACY_PATH_RE" . \
  -g '!.git/**' \
  -g '!.venv/**' \
  -g '!**/__pycache__/**' \
  -g '!**/.pytest_cache/**' \
  -g '!.planning/**' \
  -g '!dist/**' \
  -g '!build/**'
```
