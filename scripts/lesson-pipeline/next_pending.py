#!/usr/bin/env python3
"""Print the next pending entry from a lesson-sources config as JSON, or
exit 1 with a message if there isn't one. No LLM/API key involved — this
just reads the config the same way generate_lesson.py does.

Used by the /add-lesson skill in "subscription mode": Claude Code itself
does the fetch/research/write step (via its own tools, no metered API
call), and just needs to know which URL is next.

Usage:
    python3 scripts/lesson-pipeline/next_pending.py --config <path>
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lesson_pipeline.config_store import find_first_pending, load_config


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", required=True, type=Path)
    args = parser.parse_args()

    if not args.config.exists():
        print(f"error: config file not found: {args.config}", file=sys.stderr)
        return 1

    _, entries, _, _ = load_config(args.config)
    entry = find_first_pending(entries)
    if entry is None:
        print("No pending URLs found.")
        return 1

    print(json.dumps(entry, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
