---
name: recall
description: Searches the Claude Ops Notion databases (Session Log, Projects, Repo Evaluations, Capabilities) for past work and returns what was found. Use when the user refers to earlier sessions or decisions — "last time", "we already", "did we evaluate", "what did we decide about", "have we set up" — or before starting significant work, to check what's already recorded.
user-invocable: true
allowed-tools: mcp__claude_ai_Notion__notion-fetch, mcp__claude_ai_Notion__notion-search, Read
argument-hint: "<what to look up>"
---

# Claude Ops — recall

Look up prior work in the four Notion databases before treating a topic as new.

## Why structured queries first

Notion's native search is, per Notion's own docs, "not guaranteed to return everything" and
is meant for finding pages by name — not for exhaustively checking whether a record exists.
For a system-of-record that is the worst failure: a false "no prior data". So query the
**data sources** directly with filters as the primary path; use native search only for fuzzy
discovery; and never assert "nothing was recorded" until a structured query has confirmed it.

## Steps

1. **Load config** from `~/.claude/claude-ops.json` (Read tool) for the four `databases`
   data-source IDs. No config → tell the user to run `/claude-ops:setup` first, and stop.

2. **Query the relevant data source(s) with filters** (not a workspace search). Map the query:
   - decisions / "what did we do" / "last time" → **Session Log** (filter/sort by Date, title)
   - ongoing work / goals / status → **Projects** (filter by Status / Name)
   - "did we evaluate <repo>" / "is <tool> worth it" → **Repo Evaluations** (filter by Repo / Verdict)
   - "do we have" / "did we install" / "what tools" → **Capabilities** (filter by Capability / Type)
   Use the Notion data-source query (API version 2025-09-03: query the data source by its id with
   a property filter). Native `notion-search` is a fallback only when the query is fuzzy and not
   tied to one database.

3. **Progressive disclosure — don't pull full pages up front.** First retrieve a compact list
   (title, date, id, and the key select fields) so the cost is small. Then `notion-fetch` the full
   body only for the entries that actually look relevant. This keeps token cost ~10x lower than
   fetching everything.

4. **Report** concisely: what was found, from which database, with links. If a structured query
   returns nothing, say so plainly — "nothing relevant is recorded in <database>" — so the user
   knows it's a verified gap, not a missed lookup.
