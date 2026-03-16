status: passed
rationale: Phase 10 goal is achieved; README+RUNBOOK provide docs-only install/config/validation flow and smoke evidence is reproducible.
verified_by: phase-verifier
verified_on: 2026-03-16

# Phase 10 Verification Evidence

Date: 2026-03-16 (UTC+01)
Plan: 10-02
Scope: DOCS-01, DOCS-02, DOCS-03 closeout evidence

## Verification Commands

### DOCS-01: clean onboarding path (fresh shell) + prereq visibility

Result: PASS (positive path) and PASS (expected negative path clarity)

1. fresh shell prerequisite visibility + negative startup guard (missing token)

```bash
env -i HOME="$HOME" PATH="$PATH" bash -lc 'set -euo pipefail; cd ~/Workspace/tools/ya-logseq-mcp; python3 --version; uv --version; test -n "${LOGSEQ_API_TOKEN:-}" || echo "LOGSEQ_API_TOKEN not set in fresh shell"; uv run --project ~/Workspace/tools/ya-logseq-mcp ya-logseq-mcp --help >/tmp/phase10_docs_help.txt'
```

Observed output markers:
- `Python 3.12.3`
- `uv 0.10.4`
- `LOGSEQ_API_TOKEN not set in fresh shell`
- `RuntimeError: LOGSEQ_API_TOKEN environment variable is required. Set it in your MCP client config or shell environment.`

Interpretation:
- Prerequisites are explicit and runnable from a clean shell.
- Hidden prerequisite failure (missing token) is explicit and understandable.

2. fresh shell docs-style success marker using environment load and smoke

```bash
source ~/Workspace/.env && uv run pytest tests/integration/test_mcp_stdio.py::test_stdio_server_exposes_expected_tools -x -q -m integration
```

Observed output markers:
- `. [100%]`
- `1 passed in 0.54s`

Interpretation:
- With documented env loading, the onboarding path is executable and succeeds from a fresh shell session.

### DOCS-02: README MCP config shape + startup semantics

Result: PASS + negative-check guard PASS

1. README config parse and startup semantics

```bash
uv run --project ~/Workspace/tools/ya-logseq-mcp python -c 'import json,pathlib,re; t=pathlib.Path("README.md").read_text(); m=re.search(r"```json\s*(\{[\s\S]*?\})\s*```", t); assert m, "README MCP JSON snippet missing"; cfg=json.loads(m.group(1)); servers=cfg.get("mcpServers") or {}; assert servers, "mcpServers missing"; s=next(iter(servers.values())); missing=[k for k in ["command","args","cwd","env"] if k not in s]; assert not missing, missing; assert isinstance(s["args"], list) and s["args"], "args must be non-empty list"; joined=" ".join(str(x) for x in s["args"]); assert ("ya-logseq-mcp" in joined) or ("-m" in s["args"] and "ya_logseq_mcp.server" in joined), "startup semantics mismatch"; print("readme-config-parse-and-startup-ok")'
```

Observed output marker:
- `readme-config-parse-and-startup-ok`

2. negative-check guard (missing required fields in config shape)

```bash
uv run --project ~/Workspace/tools/ya-logseq-mcp python -c 's={"command":"uv","args":["run"]}; missing=[k for k in ["command","args","cwd","env"] if k not in s]; assert not missing, missing'
```

Observed output marker:
- `AssertionError: ['cwd', 'env']`

Interpretation:
- Failure conditions for incomplete MCP config fields are deterministic and readable.

### DOCS-03: smoke-check flow + escalation branch

Result: PASS for documented smoke steps and escalation path check

1. unit smoke

```bash
uv run --project ~/Workspace/tools/ya-logseq-mcp pytest tests/test_server.py -q
```

Observed output marker:
- `6 passed in 0.30s`

2. stdio integration smoke

```bash
source ~/Workspace/.env && uv run pytest tests/integration/test_mcp_stdio.py -x -q -m integration
```

Observed output marker:
- `11 passed in 9.28s`

3. smoke escalation branch present and traceable

```bash
rg -n "If smoke fails|Troubleshooting|RUNBOOK" README.md RUNBOOK.md
```

Observed output markers:
- README includes `If smoke fails`
- README references `RUNBOOK.md`
- RUNBOOK includes `Troubleshooting`

Interpretation:
- If smoke fails, the docs route users to concrete next actions and maintainer troubleshooting.

## Canonical Surface Boundary Check

Result: PASS

```bash
rg -n "canonical|onboarding|User-facing install/run/config guidance lives in `README.md`|maintainer" README.md RUNBOOK.md
```

Observed output markers:
- README positions onboarding sections (Requirements, Install, Run Locally, MCP Client Config, Smoke Check).
- RUNBOOK states: user-facing install/run/config guidance is in README and runbook is maintainer-focused.

Interpretation:
- README canonical onboarding surface is preserved; RUNBOOK remains maintainer-focused.

## Requirement Mapping

- DOCS-01: satisfied by fresh shell prereq checks, explicit missing-token failure clarity, and successful env-loaded onboarding smoke.
- DOCS-02: satisfied by machine-validated README JSON config shape (`command/args/cwd/env`) and startup semantics plus negative guard.
- DOCS-03: satisfied by passing unit + integration smoke checks and documented "If smoke fails" escalation to Troubleshooting/RUNBOOK.

## Verifier Cross-Check Addendum (2026-03-16)

Plan frontmatter requirement IDs:
- `10-01-PLAN.md`: DOCS-01, DOCS-02, DOCS-03
- `10-02-PLAN.md`: DOCS-01, DOCS-02, DOCS-03

Requirement registry cross-reference:
- `.planning/REQUIREMENTS.md` includes DOCS-01, DOCS-02, DOCS-03 and marks all complete under "Documentation and Installation UX".

Must-have artifacts/links validated in real files:
- `README.md` contains prerequisites, install, run, MCP config (`command/args/cwd/env`), smoke checks, and "If smoke fails" escalation.
- `RUNBOOK.md` keeps maintainer-only guardrails and troubleshooting, explicitly deferring user onboarding to README.
- `tests/integration/conftest.py` validates MCP config structure (`command`, `args`, `env`, `cwd`) matching README contract.
- `tests/integration/test_mcp_stdio.py` contains the documented stdio smoke entrypoint (`test_stdio_server_exposes_expected_tools`).

Spot re-validation performed by verifier:
- `uv run --project ~/Workspace/tools/ya-logseq-mcp python -c ...` => `readme-config-parse-and-startup-ok`
- `uv run --project ~/Workspace/tools/ya-logseq-mcp pytest tests/test_server.py -q` => `6 passed`
- `source ~/Workspace/.env && uv run pytest tests/integration/test_mcp_stdio.py::test_stdio_server_exposes_expected_tools -x -q -m integration` => `1 passed`

Gaps:
- None.
