---
name: setup
description: Sets up Claude Ops — creates the four Notion databases (Session Log, Projects, Repo Evaluations, Capabilities), writes their IDs to ~/.claude/claude-ops.json, and installs the SessionStart + Stop hooks into ~/.claude/settings.json so logging and recall work. Run once per machine.
disable-model-invocation: true
user-invocable: true
allowed-tools: mcp__claude_ai_Notion__notion-search, mcp__claude_ai_Notion__notion-create-database, mcp__claude_ai_Notion__notion-fetch, Read, Write, Edit, Bash
argument-hint: "[parent page name or URL (optional)]"
---

# Claude Ops — setup

Create the four Notion databases, write config, and install the hooks. Run once.

## Prerequisite

The Notion MCP connector must be connected. If `mcp__claude_ai_Notion__*` tools are
unavailable, stop and tell the user to connect Notion first (claude.ai → Connectors → Notion),
then re-run `/claude-ops:setup`.

## Steps

1. **Pick a parent page.** If the user passed one as an argument, use it. Otherwise ask
   which Notion page should hold these databases (search for it and confirm the exact page
   before creating anything — creating pages is a real side effect).

2. **Create four databases** under that parent with these properties (`select` where noted,
   else rich text unless stated):
   - **Session Log** — `Entry` (title), `Date` (date), `What we did`, `Decisions`, `Outcome`
   - **Projects** — `Name` (title), `Status` (select: Active / Paused / Done), `Domain`,
     `Started` (date), `Summary`, `Key artifacts`, `Next steps`
   - **Repo Evaluations** — `Repo` (title), `Verdict` (select: ADOPT / CHERRY-PICK / SKIP),
     `Category` (select), `Why`, `Stars / inflation`, `Install method`, `Date` (date), `Link` (url)
   - **Capabilities** — `Capability` (title), `Type` (select: skill / MCP / CLI tool / plugin / policy),
     `Status` (select: Active / Pending), `How it works`, `Location / command`,
     `Notes / cautions`, `Date` (date)

3. **Capture each database's `data_source_id`** from the create response (fetch it back if not
   returned directly). These are what `/claude-ops:recall` queries — record them carefully.

4. **Write config** to `~/.claude/claude-ops.json` with the Write tool. Read any existing file
   first and preserve unrelated keys. Shape:
   ```json
   {
     "parent_page": "<page id or url>",
     "databases": {
       "session_log": "<data_source_id>",
       "projects": "<data_source_id>",
       "repo_evaluations": "<data_source_id>",
       "capabilities": "<data_source_id>"
     },
     "thresholds": { "edits": 4, "tools": 40 }
   }
   ```

5. **Install the hooks into settings.json — do NOT rely on the plugin's hooks.** Plugin-packaged
   SessionStart hooks have their injected context silently discarded, and plugin Stop hooks fail
   to continue the turn (Claude Code issues #16538, #10412). So:
   1. Create `~/.claude/claude-ops/hooks/` and copy `reminder.py`, `stop_guard.py`, and
      `python-launcher.sh` there from this plugin's `hooks/` directory (resolvable via
      `${CLAUDE_PLUGIN_ROOT}/hooks/`). Copying to this stable path also survives plugin updates,
      which move the plugin's cache directory.
   2. Read `~/.claude/settings.json` (create `{}` if absent; **back it up first**). Merge in —
      preserving any existing hooks — a SessionStart entry (matcher `startup|resume|clear|compact`)
      running `reminder.py` and a Stop entry running `stop_guard.py`, each via the launcher with
      **absolute** paths, e.g. (forward slashes, real home dir):
      ```json
      {
        "hooks": {
          "SessionStart": [
            { "matcher": "startup|resume|clear|compact",
              "hooks": [ { "type": "command",
                "command": "bash \"<HOME>/.claude/claude-ops/hooks/python-launcher.sh\" \"<HOME>/.claude/claude-ops/hooks/reminder.py\"" } ] }
          ],
          "Stop": [
            { "hooks": [ { "type": "command",
                "command": "bash \"<HOME>/.claude/claude-ops/hooks/python-launcher.sh\" \"<HOME>/.claude/claude-ops/hooks/stop_guard.py\"" } ] }
          ]
        }
      }
      ```
      Resolve `<HOME>` to the real absolute home path. If a Claude Ops hook entry already exists,
      replace it rather than duplicating.

6. **Confirm** to the user: list the four created databases with links; note that the hooks are
   installed in settings.json and take effect next session; mention recall uses structured
   data-source queries (see `/claude-ops:recall`).

Keep it to one pass. Don't create extra databases, views, or pages beyond the four.
