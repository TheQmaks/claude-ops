#!/usr/bin/env python3
"""Stop hook for Claude Ops.

If a session did significant work but never wrote to Notion, block ONCE to make the
agent log it. Bounded by stop_hook_active + a per-session marker, so it can never loop.
Reads thresholds and the Session Log id from config. No config, or any failure, exits 0
(never breaks a session, never nags before /claude-ops:setup)."""
import sys, os, json

EDIT_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
# Infrastructure/bookkeeping calls that don't represent substantive work — excluded from
# the tool-count threshold so a trivial dialog with many of these doesn't trip the nudge.
NOISE_TOOLS = {"TodoWrite", "AskUserQuestion", "ListMcpResourcesTool"}


def config_path():
    return os.path.join(os.path.expanduser("~"), ".claude", "claude-ops.json")


def load_config():
    try:
        with open(config_path(), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0

    # Never re-block: if we already forced a continuation, let it stop.
    if data.get("stop_hook_active"):
        return 0

    cfg = load_config()
    dbs = (cfg or {}).get("databases") or {}
    session_log = dbs.get("session_log")
    if not session_log:
        return 0  # not set up yet — stay silent

    thresholds = (cfg or {}).get("thresholds") or {}
    thresh_edits = int(thresholds.get("edits", 4))
    thresh_tools = int(thresholds.get("tools", 40))

    sid = str(data.get("session_id") or "unknown")
    tpath = data.get("transcript_path")
    if not tpath or not os.path.exists(tpath):
        return 0

    marker_dir = os.path.join(os.path.expanduser("~"), ".claude", ".cache", "claude-ops-nudge")
    marker = os.path.join(marker_dir, sid)
    if os.path.exists(marker):
        return 0

    edits = tools = 0
    notion = False
    try:
        with open(tpath, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                msg = obj.get("message") or {}
                content = msg.get("content")
                if not isinstance(content, list):
                    continue
                for it in content:
                    if isinstance(it, dict) and it.get("type") == "tool_use":
                        name = it.get("name", "") or ""
                        if name not in NOISE_TOOLS:
                            tools += 1
                        if name in EDIT_TOOLS:
                            edits += 1
                        if "notion" in name.lower():
                            notion = True
    except Exception:
        return 0

    significant = edits >= thresh_edits or tools >= thresh_tools
    if significant and not notion:
        try:
            os.makedirs(marker_dir, exist_ok=True)
            open(marker, "w").close()
        except Exception:
            pass
        reason = (
            "This session looks significant, but nothing was logged to Claude Ops (Notion). "
            "Before finishing, create a Session Log entry with your Notion MCP create-pages "
            f"tool (data source {session_log}) — briefly: what we did, decisions, outcome. "
            "If there were repo verdicts or new capabilities, add them to Repo Evaluations / "
            "Capabilities too. If the work was trivial, say so in one line and finish."
        )
        print(json.dumps({"decision": "block", "reason": reason}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
