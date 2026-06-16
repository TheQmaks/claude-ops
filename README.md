# Claude Ops

A durable **Notion system-of-record** for Claude Code. Most memory plugins are local
(Obsidian vaults) or just an MCP bridge. Claude Ops adds the missing layer: **enforcement
and recall** on top of Notion — so significant work actually gets written down, and gets
read back in future sessions.

It does three things:

1. **Logs** significant work (research, repo evaluations, builds, decisions) to four Notion
   databases.
2. **Nudges** you once, before a meaningful session ends, if nothing was logged.
3. **Recalls** past decisions and verdicts in later sessions, so the same questions aren't
   re-solved from scratch.

## Requirements

- The **Notion MCP connector** (claude.ai → Connectors → Notion). Claude Ops sits on top of it.

## Install

```
/plugin marketplace add TheQmaks/claude-ops
/plugin install claude-ops@theqmaks-claude-ops
```

Third-party marketplaces don't auto-update by default. To get updates:
`/plugin` → Marketplaces → enable auto-update.

## Setup (once)

```
/claude-ops:setup
```

This asks for a parent Notion page, creates the four databases under it, writes their IDs to
`~/.claude/claude-ops.json`, and installs the SessionStart + Stop hooks into
`~/.claude/settings.json`. No IDs are hard-coded, so the plugin works for anyone.

> **Why hooks go in settings.json, not the plugin.** Claude Code currently discards the
> injected context of plugin-packaged SessionStart hooks, and plugin Stop hooks don't continue
> the turn (issues [#16538](https://github.com/anthropics/claude-code/issues/16538),
> [#10412](https://github.com/anthropics/claude-code/issues/10412)). Setup copies the hook
> scripts to `~/.claude/claude-ops/hooks/` (a stable path that survives plugin updates) and
> registers them in your settings.json — the path that works reliably.

The four databases:

| Database | Purpose |
|---|---|
| **Session Log** | What we did, decisions, outcome, date |
| **Projects** | Ongoing work, status, next steps |
| **Repo Evaluations** | Verdicts on repos/tools (adopt / cherry-pick / skip) |
| **Capabilities** | Installed skills, MCPs, CLI tools, policies |

## Usage

- **Logging** is prompted automatically. At the end of meaningful work, Claude writes a
  Session Log entry (and Repo Evaluations / Capabilities when relevant) via the Notion MCP tools.
- **Recall** runs on its own when you reference past work ("did we evaluate X?", "what did we
  decide last time?"), or on demand:

  ```
  /claude-ops:recall <what to look up>
  ```

  Recall queries the Notion **data sources directly with filters** (Notion's native search is
  not exhaustive and can falsely report "no prior data"), and uses progressive disclosure —
  a compact list first, full pages only for relevant hits — to keep token cost low.

## How it works

- `reminder.py` (SessionStart, installed in settings.json) states — as plain fact, not a
  forceful command — that the four databases are durable memory and how to query them, with
  their data-source IDs.
- `stop_guard.py` (Stop, installed in settings.json) blocks **once** if a session did significant
  work (≥ 4 edits or ≥ 40 tool calls, configurable) but never touched Notion. Bounded by a
  per-session marker and `stop_hook_active` — it can't loop, and any failure exits 0.
- Thresholds live in `~/.claude/claude-ops.json` under `thresholds`.

## License

MIT.
