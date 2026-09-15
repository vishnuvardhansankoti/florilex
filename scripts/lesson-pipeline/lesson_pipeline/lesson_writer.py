"""Turns the LLM's structured lesson dict into a real .mdx file inside the
right apps/<topic>/src/content/lessons/phases/<phase>/ directory, matching
the schema in apps/<topic>/src/content/config.ts.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
APPS_ROOT = REPO_ROOT / "apps"

IMPORTS = [
    'import Callout from "@florilex/tutorial-kit/components/Callout.astro";',
    'import Formula from "@florilex/tutorial-kit/components/Formula.astro";',
    'import WorkTask from "@florilex/tutorial-kit/components/WorkTask.astro";',
    'import Solution from "@florilex/tutorial-kit/components/Solution.astro";',
]


class LessonWriteError(RuntimeError):
    pass


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "lesson"


def _topic_dir(topic: str) -> Path:
    app_dir = APPS_ROOT / topic
    if not app_dir.is_dir():
        available = ", ".join(sorted(p.name for p in APPS_ROOT.iterdir() if p.is_dir()))
        raise LessonWriteError(f"No apps/{topic} directory (available topics: {available})")
    return app_dir


def _phases_dir(topic: str) -> Path:
    return _topic_dir(topic) / "src" / "content" / "lessons" / "phases"


def _parse_frontmatter(mdx_text: str) -> dict:
    match = re.match(r"^---\n(.*?)\n---\n", mdx_text, re.DOTALL)
    if not match:
        return {}
    return yaml.safe_load(match.group(1)) or {}


def _existing_lessons(topic: str) -> list[dict]:
    phases_dir = _phases_dir(topic)
    lessons = []
    if phases_dir.is_dir():
        for mdx_path in phases_dir.rglob("*.mdx"):
            frontmatter = _parse_frontmatter(mdx_path.read_text())
            frontmatter["_phase_dir"] = mdx_path.parent.name
            lessons.append(frontmatter)
    return lessons


def _next_numbers(topic: str, phase_slug: str) -> tuple[int, int]:
    lessons = _existing_lessons(topic)
    global_max_order = max((int(l.get("order", 0)) for l in lessons), default=0)
    same_phase_count = sum(1 for l in lessons if l.get("_phase_dir") == phase_slug)
    return global_max_order + 1, same_phase_count + 1


def render_mdx(data: dict, *, source_url: str, pub_date: str, order: int, lesson_number: int) -> str:
    frontmatter = {
        "title": data["title"],
        "subtitle": data.get("subtitle"),
        "summary": data["summary"],
        "phase": data["phaseSlug"],
        "phaseTitle": data["phaseTitle"],
        "order": order,
        "lessonNumber": lesson_number,
        "pubDate": pub_date,
        "hook": data.get("hook"),
        "hookCredit": data.get("hookCredit"),
        "sourceUrl": source_url,
    }
    frontmatter = {k: v for k, v in frontmatter.items() if v not in (None, "")}
    frontmatter_yaml = yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True).strip()

    body_parts = []
    for i, section in enumerate(data.get("sections", []), start=1):
        heading = section["heading"]
        body_md = section["body_md"].strip()
        body_parts.append(
            f'<section class="lesson">\n'
            f'<div class="sec-head"><span class="sec-num">{i}</span>'
            f'<h2 class="sec-title">{heading}</h2></div>\n\n'
            f"{body_md}\n\n"
            f"</section>"
        )

    for task in data.get("tasks", []):
        prompt_md = task["prompt_md"].strip()
        solution_md = task["solution_md"].strip()
        body_parts.append(
            f'<WorkTask label="{task["label"]}" title="{task["title"]}">\n\n'
            f"{prompt_md}\n\n"
            f"<Solution>\n\n{solution_md}\n\n</Solution>\n"
            f"</WorkTask>"
        )

    return (
        "---\n"
        + frontmatter_yaml
        + "\n---\n\n"
        + "\n".join(IMPORTS)
        + "\n\n"
        + "\n\n".join(body_parts)
        + "\n"
    )


def write_lesson(topic: str, data: dict, *, source_url: str, pub_date: str) -> Path:
    phase_slug = slugify(data["phaseSlug"])
    lesson_slug = slugify(data["lessonSlug"])

    order, lesson_number = _next_numbers(topic, phase_slug)
    phase_dir = _phases_dir(topic) / phase_slug
    phase_dir.mkdir(parents=True, exist_ok=True)

    file_path = phase_dir / f"{lesson_number:02d}-{lesson_slug}.mdx"
    if file_path.exists():
        raise LessonWriteError(f"{file_path} already exists — refusing to overwrite")

    file_path.write_text(render_mdx(data, source_url=source_url, pub_date=pub_date, order=order, lesson_number=lesson_number))
    return file_path
