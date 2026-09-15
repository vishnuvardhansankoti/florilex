#!/usr/bin/env python3
"""Pick the next pending URL from a lesson-sources config, elaborate on and
summarize it via a config-driven LLM (cloud or local, with optional web
search), and write the result as a new Florilex lesson .mdx file.

Usage:
    python3 scripts/lesson-pipeline/generate_lesson.py --config scripts/lesson-pipeline/lesson-sources.yaml

See scripts/lesson-pipeline/README.md for the config file schema.
"""

from __future__ import annotations

import argparse
import datetime
import os
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lesson_pipeline.config_store import find_first_pending, load_config, save_config
from lesson_pipeline.fetch_page import fetch_page
from lesson_pipeline.lesson_writer import LessonWriteError, write_lesson
from lesson_pipeline.llm_client import LLMError, elaborate_and_summarize, resolve_llm_config


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", required=True, type=Path, help="Path to the urls config (.yaml/.yml/.json/.csv)")
    parser.add_argument("--dry-run", action="store_true", help="Write the lesson file but don't mark the URL processed")
    args = parser.parse_args()

    if not args.config.exists():
        print(f"error: config file not found: {args.config}", file=sys.stderr)
        return 1

    data, entries, llm_cfg_raw, fmt = load_config(args.config)

    entry = find_first_pending(entries)
    if entry is None:
        print("No pending URLs found — nothing to do.")
        return 0

    url = entry.get("url", "")
    topic = entry.get("topic", "")
    if not topic:
        print(f"error: entry for {url!r} has no 'topic' field", file=sys.stderr)
        return 1

    llm_cfg = resolve_llm_config(llm_cfg_raw)
    print(f"Processing {url}  (topic={topic}, provider={llm_cfg['provider']}, model={llm_cfg['model']})")

    try:
        print("Fetching page...")
        title, text = fetch_page(url)
    except requests.exceptions.RequestException as e:
        print(f"error: could not fetch {url}: {e}", file=sys.stderr)
        return 1

    try:
        print("Calling LLM (elaborate + summarize)...")
        result = elaborate_and_summarize(llm_cfg, topic=topic, url=url, page_title=title, page_text=text)

        if entry.get("phase"):
            result["phaseSlug"] = entry["phase"]
        if entry.get("phaseTitle"):
            result["phaseTitle"] = entry["phaseTitle"]

        pub_date = datetime.date.today().isoformat()
        path = write_lesson(topic, result, source_url=url, pub_date=pub_date)
    except (LLMError, LessonWriteError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    print(f"Wrote {os.path.relpath(path)}")

    if args.dry_run:
        print("--dry-run set: not updating config status.")
    else:
        entry["status"] = "processed"
        save_config(args.config, data, entries, fmt)
        print(f"Marked {url} as processed in {args.config}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
