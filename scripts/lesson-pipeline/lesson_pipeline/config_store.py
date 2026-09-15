"""Load/save the lesson-sources config (yaml/yml/json/csv) in place.

YAML and JSON share one shape: {"llm": {...}, "urls": [{...}, ...]}.
CSV has no room for the "llm" block, so csv-configured runs fall back to
env vars / defaults for LLM settings (see llm_client.resolve_llm_config).
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import yaml

PROCESSED_VALUES = {"processed", "done", "complete", "completed"}


def is_processed(entry: dict) -> bool:
    return str(entry.get("status", "")).strip().lower() in PROCESSED_VALUES


def load_config(path: Path):
    """Returns (data, entries, llm_config, fmt).

    `data` is the full parsed document for yaml/json (None for csv) — pass
    it back into save_config so the llm block and any other top-level keys
    survive the round trip. `entries` is the list of url rows (already
    embedded in `data["urls"]` for yaml/json, so mutating it in place is
    enough).
    """
    suffix = path.suffix.lower()
    if suffix in (".yaml", ".yml"):
        data = yaml.safe_load(path.read_text()) or {}
        data.setdefault("urls", [])
        return data, data["urls"], data.get("llm", {}) or {}, "yaml"
    if suffix == ".json":
        data = json.loads(path.read_text() or "{}")
        data.setdefault("urls", [])
        return data, data["urls"], data.get("llm", {}) or {}, "json"
    if suffix == ".csv":
        with path.open(newline="") as f:
            entries = list(csv.DictReader(f))
        return None, entries, {}, "csv"
    raise ValueError(f"Unsupported config format: {suffix!r} (use .yaml, .json, or .csv)")


def save_config(path: Path, data: dict | None, entries: list[dict], fmt: str) -> None:
    if fmt == "yaml":
        data["urls"] = entries
        path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True))
    elif fmt == "json":
        data["urls"] = entries
        path.write_text(json.dumps(data, indent=2) + "\n")
    elif fmt == "csv":
        if not entries:
            return
        fieldnames = list(entries[0].keys())
        with path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(entries)
    else:
        raise ValueError(f"Unsupported config format: {fmt!r}")


def find_first_pending(entries: list[dict]) -> dict | None:
    for entry in entries:
        if entry.get("url") and not is_processed(entry):
            return entry
    return None
