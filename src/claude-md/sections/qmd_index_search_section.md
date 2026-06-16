---
section_name: Repo Index Search
---

<!-- ============================================================ -->
<!-- QMD INDEX — append to existing CLAUDE.md                     -->
<!-- ============================================================ -->

## Repo Index Search 

### Search Priority

Always follow this order — do not skip to grep/glob/cat/Read without exhausting the steps above it:

**1. qmd local** (always try first with qmd commands)
- `qmd search "<keywords>"` — BM25 keyword search
- `qmd vsearch "<question>"` — semantic search
- `qmd query "<keywords>" — semantic search, Hybrid: FTS + Vector + Query Expansion + Re-ranking (Ollama required)
- `get "<filepath>"` — retrieve full document by path  

This hits the local `index.sqlite` on WSL via the qmd MCP already configured in your environment. Fast, no network required.

If results look outdated, inform the user: "Index may be stale — run `qpi sync <REPO_NAME>` and qmd embed from your WSL terminal." Do not re-index within this session.

**2. qmd Pi** (if local returns no relevant results):

Skip this step entirely and go to step 3 if any of the following apply:
- This repo is not registered in `~/.config/qmd-pi/repos.toml`
- Tailscale is offline (Pi unreachable)
- The Pi MCP is down

Do NOT use `qmd_query` — it requires Ollama which only runs on desktop.
Do not retry, do not diagnose — just move to step 3.

Otherwise use the same `search` / `vector_search` / `get` calls via the Pi endpoint:
- qmd Pi: http://100.126.32.4:3100/mcp (Tailscale, streamable HTTP transport)

**3. graphify** (if both qmd instances return no relevant results and `graphify-out/graph.json` exists):
→ `graphify query "<question>"` — scoped subgraph for structural/relational questions
→ `graphify path "<A>" "<B>"` — relationship between two entities
→ `graphify explain "<concept>"` — focused concept summary
→ Read `graphify-out/GRAPH_REPORT.md` only for broad architecture review

**4. Local file access** (last resort only):
- You need uncommitted changes not yet in the index
- A specific file was already identified by qmd and you need its full content
- All above steps returned nothing useful
QMDSECTION
```