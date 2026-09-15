#!/usr/bin/env bash
# Thin wrapper so the lesson-generation pipeline can be run as a plain shell
# command (as well as via the Claude Code /grill-me skill).
#
# Usage: scripts/lesson-pipeline/grill-me.sh [config-path] [-- extra args to generate_lesson.py]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ $# -gt 0 ]; then
  CONFIG="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
  shift
else
  CONFIG="$SCRIPT_DIR/lesson-sources.yaml"
fi

cd "$SCRIPT_DIR"

if [ ! -f "$CONFIG" ]; then
  echo "error: config file not found: $CONFIG" >&2
  echo "Copy lesson-sources.example.yaml to $CONFIG and add URLs first." >&2
  exit 1
fi

PYTHON=".venv/bin/python3"
if [ ! -x "$PYTHON" ]; then
  echo "error: scripts/lesson-pipeline/.venv not found." >&2
  echo "Set it up first, from the repo root:" >&2
  echo "  uv venv scripts/lesson-pipeline/.venv" >&2
  echo "  uv pip install --python scripts/lesson-pipeline/.venv/bin/python3 -r scripts/lesson-pipeline/requirements.txt" >&2
  exit 1
fi

"$PYTHON" generate_lesson.py --config "$CONFIG" "$@"
