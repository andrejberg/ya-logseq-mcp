# Feature Landscape

**Domain:** MCP server for Logseq knowledge graph (replacing graphthulhu)
**Researched:** 2026-03-09
**Overall confidence:** HIGH (well-scoped brownfield rewrite with clear reference implementation)

## Table Stakes

Features users expect. Missing = product feels incomplete. Derived from: every Logseq MCP server in the ecosystem provides these, graphthulhu already had them, and they are required for the daily-driver workflow.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| `get_page` (deduplicated block tree) | Core read operation. Every Logseq MCP has it. graphthulhu's version is broken (4-8x duplication). | Medium | UUID-based dedup is the primary motivation for this rewrite. Must handle `getPageBlocksTree` correctly. |
| `get_block` (single block by UUID) | Needed for targeted reads after finding blocks via query. All competitors have it. | Low | Straightforward API passthrough with optional children. |
| `list_pages` (with filters) | Discovery tool. ergut/mcp-logseq, graphthulhu, dailydaniel all have it. | Low | Add namespace/tag/property filters to avoid dumping entire graph. |
| `get_references` (backlinks) | Backlinks are Logseq's core value prop. Every competitor exposes this. | Low | Direct `getPageLinkedReferences` passthrough. |
| `query` (raw DataScript) | Power-user escape hatch. saichaitanyam/LogseqMCP and ergut/mcp-logseq both expose it. | Low | Passthrough to `datascriptQuery`. No query building, just execution. |
| `find_by_tag` | Tag-based retrieval is fundamental to Logseq workflows. | Low | DataScript query, proven pattern from graphthulhu. |
| `query_properties` | Property-based queries power structured workflows (task management, project tracking). | Low | DataScript query, proven pattern from graphthulhu. |
| `page_create` | All competitors have it. Required for automation workflows. | Medium | Must handle properties + initial blocks correctly. Markdown-to-blocks conversion is a differentiator (see below), but basic creation is table stakes. |
| `block_append` | Core write operation. Every Logseq MCP with write support has it. | Medium | Must handle both flat strings and nested `{content, properties, children}`. Single tool for both (graphthulhu had two). |
| `block_update` | Required for modifying existing content. All write-capable competitors have it. | Low | UUID-targeted update via `updateBlock`. |
| `block_delete` | Required for content cleanup. All write-capable competitors have it. | Low | UUID-targeted delete via `removeBlock`. |
| `delete_page` | Page lifecycle management. Most competitors have it. | Low | Direct API call. |
| `rename_page` | Logseq auto-updates links on rename. ergut/mcp-logseq has it. Essential for refactoring. | Low | Direct API call. Logseq handles link updates. |
| `move_block` | Block reorganization. Needed for structural edits. | Medium | Positioning logic (before/after/child) adds complexity. |
| `health` (connectivity check) | Standard MCP practice. Every production server needs a health check. | Low | Ping Logseq, return graph name + page count. |
| `journal_today` | Journal pages are Logseq's daily workflow. joelhooks/logseq-mcp-tools exposes journal features. | Low | Get or create today's page. Date format handling is the tricky part. |
| `journal_append` | Appending to journal is the most common daily write operation. | Low | Reuses `block_append` logic with date-based page resolution. |
| Error messages as tool results | MCP best practice: return errors as `isError: true` tool results, not exceptions. Agents learn from error strings. | Low | Pattern: "Page not found. Check spelling or use list_pages to browse." |

## Differentiators

Features that set this product apart from other Logseq MCP servers. Not universally expected, but provide concrete value for this workspace's workflow.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Block deduplication by UUID** | THE reason for the rewrite. No other Logseq MCP explicitly addresses this. graphthulhu returns blocks 4-8x. | Medium | Walk block tree, track seen UUIDs, skip duplicates. This is the core correctness fix. |
| **Lean output by default** | graphthulhu always enriches with parsed links/tags/ancestors. Other servers (ergut) return verbose content. Lean output saves context window. | Low | Simply don't parse/enrich. Return raw block content + structure only. Aligns with MCP "Less is More" pattern. |
| **Unified `block_append`** | graphthulhu had two separate tools (flat vs nested). Most competitors only handle flat strings. Single tool that accepts both reduces tool count and agent confusion. | Medium | Detect input format (string vs object) and handle accordingly. |
| **Journal date format resilience** | Logseq uses locale-dependent date formats. graphthulhu struggled with this. | Medium | Try multiple formats: `"Mar 8th, 2026"`, `"March 8th, 2026"`, `"2026-03-08"`, `"March 8, 2026"`. Fail gracefully with helpful error. |
| `journal_range` (date range queries) | joelhooks/logseq-mcp-tools has `getJournalSummary`. Range queries are useful for weekly reviews, sprint planning. | Medium | Resolve date range to journal page names, fetch each. |
| **Workspace-aware kanban tools** | No other Logseq MCP has kanban support. `kanban_get`, `kanban_move`, `kanban_add_task`, `kanban_list` know the 4 standard columns. | High | Domain-specific: hardcodes BACKLOG/SPRINT BACKLOG/IN PROGRESS/FINISHED columns. Only valuable for this workspace's conventions. |
| **Workspace-aware task properties** | `kanban_add_task` knows the property schema (`type::`, `project::`, `effort::`, `dod::`, etc.). No guessing. | Medium | Embedded schema validation. Prevents malformed tasks. |
| **Template CRUD + apply** | No other Logseq MCP server has template support. Logseq's `App.*` template API is underutilized. | Medium | 5 tools: list, get, create, delete, apply. Uses `App.getCurrentGraphTemplates`, etc. |
| **DataScript over brute-force search** | graphthulhu and ergut/mcp-logseq both have brute-force `search` that scans all pages. DataScript queries are faster and more precise. | Low | Already have `query`, `find_by_tag`, `query_properties`. No need for scan-all-pages search. |
| **Async throughout** | graphthulhu uses sync Go HTTP. dailydaniel and ergut use sync Python requests. Async `httpx` enables connection pooling and concurrent operations. | Low | Already chosen in architecture. Marginal practical benefit for single-user server, but correct design. |
| **Flat argument schemas** | MCP best practice (philschmid): avoid nested dicts, use top-level primitives with Literal types and enums. Reduces agent hallucination. | Low | Design choice applied across all tools. |

## Anti-Features

Features to explicitly NOT build. Each has a clear reason.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Brute-force `search` tool** (scan all pages) | Slow, wasteful, produces huge responses that blow context windows. graphthulhu had this. ergut/mcp-logseq has this. It is the wrong pattern. | Use `query` (DataScript), `find_by_tag`, `query_properties` for targeted retrieval. |
| **Content parsing / link extraction** | graphthulhu parsed block content to extract `[[links]]`, `#tags`, property values. This is enrichment the agent does not need -- it can read the markdown. Wastes context window. | Return raw block content. The agent (or calling code) can parse if needed. |
| **In-memory graph analysis** | joelhooks `analyzeGraph`, `findKnowledgeGaps`, `suggestConnections` build in-memory graph representations. Complex, fragile, duplicates what Logseq already knows. | Use DataScript queries against Logseq's own index. It already has the graph. |
| **AI-powered analysis tools** | joelhooks `smartQuery`, `analyzeJournalPatterns`, `suggestConnections` use AI to analyze the graph. An MCP server should provide data, not interpretation. The LLM calling the MCP can do its own analysis. | Return raw data. Let the calling LLM do analysis. |
| **Natural language query translation** | joelhooks `smartQuery` converts NL to DataScript. Unreliable, adds latency, and the calling LLM can construct DataScript itself given examples. | Expose raw `query` tool with good documentation/examples in the tool description. |
| **Obsidian backend** | graphthulhu supported both Logseq and Obsidian. ~40% dead code. This server is Logseq-only. | Not applicable. |
| **Flashcard / whiteboard / decision tools** | graphthulhu had these. Never used in this workspace. Dead weight. | Not applicable. |
| **Markdown-to-blocks auto-conversion** | ergut/mcp-logseq converts markdown headings/lists into Logseq blocks automatically. Sounds nice but is fragile and opinionated -- different users expect different nesting. | Accept block content as-is. Let the caller format correctly (the caller is an LLM that knows Logseq formatting via skills). |
| **Vault/graph caching** | cyanheads/obsidian-mcp-server has an in-memory cache. Adds stale-data bugs, complexity. Logseq API is local and fast. | Hit the API directly every time. Stateless server. |
| **Multiple transport modes** | cyanheads supports stdio + HTTP + SSE. For a single-user local MCP server, stdio is the only transport that matters. | stdio only (MCP SDK default). |
| **Privacy-first log sanitization** | ergut/mcp-logseq sanitizes logs. Overkill for a single-user local server where the user owns the graph. | Standard Python logging. No sanitization needed. |
| **Tool count > 20 initially** | MCP best practice: 5-15 tools per server. 27 tools is high. Ship core + write + journal first (18 tools), add kanban/templates in v2. | Phase the rollout: v1 = 18 tools (core 7 + write 7 + journal 3 + health 1). v2 = kanban 4 + templates 5. |

## Feature Dependencies

```
health → (none)                          # Must work first, validates connectivity

get_page → client.py, types.py           # Foundation for all reads
get_block → client.py, types.py
list_pages → client.py, types.py
get_references → client.py, types.py
query → client.py                        # Raw DataScript, no type parsing needed
find_by_tag → query                      # Built on DataScript query
query_properties → query                 # Built on DataScript query

page_create → client.py, types.py        # Write tools depend on client
block_append → client.py, types.py       # Core write, used by journal_append
block_update → client.py
block_delete → client.py
delete_page → client.py
rename_page → client.py
move_block → client.py

journal_today → get_page, page_create    # Needs page read + create
journal_append → journal_today, block_append  # Needs page resolution + block write
journal_range → journal_today            # Iterates over date range

kanban_get → get_page, query_properties  # Reads board page + queries tasks
kanban_move → move_block                 # Moves blocks between columns
kanban_add_task → block_append           # Creates task block with properties
kanban_list → query_properties           # Queries tasks by status/project

template_list → client.py               # App.getCurrentGraphTemplates
template_get → client.py                # App.getTemplate
template_create → client.py             # App.createTemplate
template_delete → client.py             # App.removeTemplate
template_apply → client.py              # App.insertTemplate
```

## MVP Recommendation

**v1 (swap threshold -- replace graphthulhu):**

Prioritize these 18 tools in order:

1. `health` -- validates end-to-end connectivity (foundation)
2. `get_page` with UUID deduplication -- the reason for the rewrite
3. `get_block` -- targeted block reads
4. `list_pages` -- page discovery
5. `get_references` -- backlinks
6. `query` -- DataScript escape hatch
7. `find_by_tag` -- tag-based retrieval
8. `query_properties` -- property-based retrieval
9. `page_create` -- page lifecycle
10. `block_append` -- core write (unified flat + nested)
11. `block_update` -- block modification
12. `block_delete` -- block cleanup
13. `delete_page` -- page cleanup
14. `rename_page` -- page refactoring
15. `move_block` -- block reorganization
16. `journal_today` -- daily workflow
17. `journal_append` -- daily writes
18. `journal_range` -- date range reads

**v2 (after swap, when needed):**

Defer these 9 tools:

- `kanban_get`, `kanban_move`, `kanban_add_task`, `kanban_list` -- workspace-specific, not daily-driver yet
- `template_list`, `template_get`, `template_create`, `template_delete`, `template_apply` -- uses underutilized Logseq API, add when template workflow matures

**Rationale:** The v1 set covers 100% of daily-driver operations (read pages, write blocks, manage journal). The v2 set is workspace-convention-specific (kanban columns, task schema) and can be added without architectural changes since the tool modules are already stubbed.

## Competitive Landscape Summary

| Server | Language | Tools | Strengths | Weaknesses |
|--------|----------|-------|-----------|------------|
| ergut/mcp-logseq | TypeScript | 15 | Markdown parsing, namespace tree, mature | Brute-force search, no dedup, no journal tools |
| joelhooks/logseq-mcp-tools | TypeScript | 11 | AI analysis, journal summary, graph insights | AI-in-MCP anti-pattern, no write tools, no block-level ops |
| dailydaniel/logseq-mcp | Python | ~8 | Simple, Python, block positioning | Minimal feature set, no query tools, no journal |
| saichaitanyam/LogseqMCP | Python | ~6 | FastMCP, DataScript support | Minimal, read-focused, no write tools |
| graphthulhu (incumbent) | Go | ~27 | Feature-complete, battle-tested queries | Block duplication bug, verbose output, Obsidian dead weight |
| **logseq-mcp (this)** | Python | 18 (v1) | Correct blocks, lean output, async, workspace-aware | New, untested, single-user scope |

This server's competitive advantage is not feature count -- it is correctness. No other implementation addresses the block duplication issue or optimizes for context window efficiency.

## Sources

- [ergut/mcp-logseq](https://github.com/ergut/mcp-logseq) -- 15-tool TypeScript Logseq MCP (HIGH confidence)
- [joelhooks/logseq-mcp-tools](https://github.com/joelhooks/logseq-mcp-tools) -- AI-analysis focused Logseq MCP (HIGH confidence)
- [saichaitanyam/LogseqMCP](https://github.com/saichaitanyam/LogseqMCP) -- FastMCP Python Logseq server (HIGH confidence)
- [dailydaniel/logseq-mcp](https://github.com/dailydaniel/logseq-mcp) -- Simple Python Logseq MCP (MEDIUM confidence)
- [cyanheads/obsidian-mcp-server](https://github.com/cyanheads/obsidian-mcp-server) -- Obsidian MCP reference for feature comparison (HIGH confidence)
- [MCP Best Practices - philschmid](https://www.philschmid.de/mcp-best-practices) -- Tool design patterns (HIGH confidence)
- [Less is More - Klavis AI](https://www.klavis.ai/blog/less-is-more-mcp-design-patterns-for-ai-agents) -- MCP design patterns (HIGH confidence)
- [Best MCP Servers for Knowledge Bases 2026](https://www.desktopcommander.app/blog/best-mcp-servers-for-knowledge-bases-in-2026/) -- Ecosystem overview (MEDIUM confidence)
