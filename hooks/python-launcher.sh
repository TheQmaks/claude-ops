#!/usr/bin/env bash
# Cross-platform python launcher for Claude Ops hooks.
# Finds an available python interpreter and runs the given script.
# Any failure exits 0 so a missing interpreter never breaks a session.
script="$1"
shift
for py in python3 python py; do
  if command -v "$py" >/dev/null 2>&1; then
    exec "$py" "$script" "$@"
  fi
done
echo "claude-ops: no python interpreter found (python3/python/py)" >&2
exit 0
