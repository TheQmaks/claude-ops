#!/usr/bin/env python3
"""SessionStart hook for Claude Ops.

Stdout from a SessionStart hook is injected into the session context. We use it to
state, as plain fact, that the four Notion databases are the durable memory store and
how to query them. Phrasing is deliberately factual, not imperative: Anthropic's hook
docs note that out-of-band command phrasing ("you MUST...") can trip Claude's
prompt-injection defenses and get surfaced to the user instead of acted on, and recent
Opus models over-trigger on forceful caps. So this reads as context, not an order.

Install: this script is registered in ~/.claude/settings.json by /claude-ops:setup
(NOT shipped as a plugin hook — plugin-packaged SessionStart hooks have their output
silently discarded; see issue #16538).

Reads database IDs from the config written by /claude-ops:setup. If there is no
config yet, it points the user at setup instead of nagging. Any failure prints
nothing and exits 0 — a hook must never break a session."""
import sys, os, json


def config_path():
    return os.path.join(os.path.expanduser("~"), ".claude", "claude-ops.json")


def load_config():
    try:
        with open(config_path(), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def main():
    cfg = load_config()
    dbs = (cfg or {}).get("databases") or {}

    if not dbs:
        print(
            "[Claude Ops] Not configured yet. Run /claude-ops:setup once to create the "
            "four Notion databases (Session Log, Projects, Repo Evaluations, Capabilities) "
            "and enable durable logging + recall. Requires the Notion MCP connector."
        )
        return 0

    def line(key, label):
        sid = dbs.get(key)
        return f"- {label}: {sid}" if sid else None

    rows = [
        line("session_log", "Session Log     "),
        line("projects", "Projects        "),
        line("repo_evaluations", "Repo Evaluations"),
        line("capabilities", "Capabilities    "),
    ]
    rows = [r for r in rows if r]

    print(
        "[Claude Ops — durable Notion system-of-record]\n"
        "Durable project memory for this user lives in four Notion databases. Prior "
        "sessions, decisions, repo verdicts, and set-up capabilities are recorded there, "
        "and a given record may not be present in this conversation's context. The "
        "/claude-ops:recall skill queries them; a structured query of the data sources "
        "below is the reliable way to confirm whether prior work exists before treating "
        "a topic as new. Significant work (research, repo evals, builds, decisions) is "
        "normally logged to the Session Log at the end of a session.\n"
        "Data-source IDs:\n" + "\n".join(rows)
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
