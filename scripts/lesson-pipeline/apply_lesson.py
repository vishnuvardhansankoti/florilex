#!/usr/bin/env python3
"""Write an already-composed lesson dict to disk and mark its source URL
processed. No LLM/API key involved — this is the second half of
generate_lesson.py's work, split out so a caller that already did the
elaborate/summarize step itself (e.g. Claude Code running under a Claude
subscription instead of a metered API key) can drive it directly.

Usage:
    python3 scripts/lesson-pipeline/apply_lesson.py \\
        --config scripts/lesson-pipeline/lesson-sources.yaml \\
        --url https://example.com/article \\
        --data lesson.json      # or: --data - to read JSON from stdin

`--data` must be a JSON object matching the schema documented in
scripts/lesson-pipeline/README.md (title, subtitle, summary, hook,
hookCredit, phaseTitle, phaseSlug, lessonSlug, sections, tasks).
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lesson_pipeline.config_store import is_processed, load_config, save_config
from lesson_pipeline.lesson_writer import LessonWriteError, write_lesson


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", required=True, type=Path, help="Path to the urls config (.yaml/.yml/.json/.csv)")
    parser.add_argument("--url", required=True, help="The source URL this lesson was generated from (must match an entry in --config)")
    parser.add_argument("--data", required=True, help="Path to a JSON file with the lesson dict, or '-' to read JSON from stdin")
    parser.add_argument("--dry-run", action="store_true", help="Write the lesson file but don't mark the URL processed")
    args = parser.parse_args()

    if not args.config.exists():
        print(f"error: config file not found: {args.config}", file=sys.stderr)
        return 1

    data, entries, _, fmt = load_config(args.config)

    entry = next((e for e in entries if e.get("url") == args.url), None)
    if entry is None:
        print(f"error: no entry with url {args.url!r} in {args.config}", file=sys.stderr)
        return 1
    if is_processed(entry):
        print(f"error: {args.url!r} is already marked processed in {args.config}", file=sys.stderr)
        return 1

    topic = entry.get("topic", "")
    if not topic:
        print(f"error: entry for {args.url!r} has no 'topic' field", file=sys.stderr)
        return 1

    raw = sys.stdin.read() if args.data == "-" else Path(args.data).read_text()
    try:
        result = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"error: --data is not valid JSON: {e}", file=sys.stderr)
        return 1

    if entry.get("phase"):
        result["phaseSlug"] = entry["phase"]
    if entry.get("phaseTitle"):
        result["phaseTitle"] = entry["phaseTitle"]

    try:
        pub_date = datetime.date.today().isoformat()
        path = write_lesson(topic, result, source_url=args.url, pub_date=pub_date)
    except (LessonWriteError, KeyError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    print(f"Wrote {os.path.relpath(path)}")

    if args.dry_run:
        print("--dry-run set: not updating config status.")
    else:
        entry["status"] = "processed"
        save_config(args.config, data, entries, fmt)
        print(f"Marked {args.url} as processed in {args.config}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
