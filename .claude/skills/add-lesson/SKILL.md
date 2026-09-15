---
name: add-lesson
description: Fetch the next pending URL from a Florilex lesson-sources config, research and write an original lesson based on it, and save it as a new .mdx file in the right apps/<topic> directory. Runs on the invoking Claude session by default (no metered API key needed) — a config-driven external LLM is also available if requested.
---

# add-lesson

Takes the next unprocessed URL from a lesson-sources config file
(YAML/JSON/CSV), researches and writes an original lesson based on it,
and saves the result as a new `.mdx` file in
`apps/<topic>/src/content/lessons/phases/...`, then marks that URL
`processed` in the config. Full config schema and design notes are in
`scripts/lesson-pipeline/README.md`.

There are two ways to do the research-and-write step. **Default to mode A**
unless the user's config or request clearly calls for mode B — most users
running this locally have a Claude subscription (Pro/Max) but no metered
Anthropic API key, and mode A costs them nothing beyond that subscription.

- **Mode A — you do it** (default, no API key required): you fetch the
  page and research it yourself, using your own `WebFetch`/`WebSearch`
  tools, running on whatever's invoking this skill (your Claude
  subscription). You compose the lesson JSON yourself, then hand it to
  `apply_lesson.py`, which just does file placement and config
  bookkeeping — no LLM call, no API key.
- **Mode B — an external LLM does it**: `generate_lesson.py` calls a
  config-driven LLM (Anthropic/OpenAI API key, or a local/Ollama model)
  to do the research and writing, non-interactively. Use this only if the
  user asks for a specific external provider/model, or if this needs to
  run somewhere without a live Claude session (e.g. a cron job or CI).

## Setup (both modes)

Confirm `scripts/lesson-pipeline/.venv/bin/python3` exists — both modes'
supporting scripts (`config_store`, `lesson_writer`) live in that venv.
If not, set it up from the repo root:
```bash
uv venv scripts/lesson-pipeline/.venv
uv pip install --python scripts/lesson-pipeline/.venv/bin/python3 -r scripts/lesson-pipeline/requirements.txt
```
(fall back to `python3 -m venv` + `pip install` only if `uv` isn't on
PATH). Don't install into a bare global `python3`/`pip` — the deps here
(`anthropic`/`openai`) have caused real dependency conflicts in a shared
global environment before.

Resolve the config path: use `args` if the user passed one, otherwise
default to `scripts/lesson-pipeline/lesson-sources.yaml`. If that doesn't
exist, check for `lesson-sources.example.yaml` in the same directory and
tell the user to `cp` it to `lesson-sources.yaml` and add real URLs —
don't run against the example file itself.

## Mode A steps (default)

1. Find the next pending entry:
   ```bash
   scripts/lesson-pipeline/.venv/bin/python3 scripts/lesson-pipeline/next_pending.py --config <config-path>
   ```
   This prints a JSON object with `url` and `topic` (and optionally
   `phase`/`phaseTitle`). If it prints "No pending URLs found.", tell the
   user and stop.

2. Fetch the URL with your `WebFetch` tool and read it. Use `WebSearch`
   as needed to check facts, fill gaps the article doesn't cover, or
   confirm the material is current — don't just paraphrase the article.

3. Write an original lesson teaching the underlying ideas from first
   principles (matching this repo's house style — see existing lessons
   under `apps/<topic>/src/content/lessons/phases/` for tone/structure).
   Compose it as a JSON object with exactly this shape:
   ```json
   {
     "title": "lesson title, inline <em>...</em> allowed for emphasis",
     "subtitle": "one-sentence subtitle, inline HTML allowed",
     "summary": "2-4 sentence plain-text summary, no HTML tags",
     "hook": "optional short punchy pull-quote, or omit",
     "hookCredit": "optional attribution for the hook, or omit",
     "phaseTitle": "human phase title, e.g. 'Phase 02 — Attention'",
     "phaseSlug": "kebab-case slug matching phaseTitle, e.g. '02-attention'",
     "lessonSlug": "kebab-case slug for this lesson, no number prefix",
     "sections": [
       {"heading": "Section heading", "body_md": "one or more paragraphs of markdown. At most one <Callout label=\"...\"> or <Formula name=\"...\"> block per section, only if genuinely useful."}
     ],
     "tasks": [
       {"label": "Task 1 · Implement", "title": "short task title", "prompt_md": "markdown task prompt", "solution_md": "markdown solution, fenced code blocks allowed"}
     ]
   }
   ```
   Write 3-6 sections and 1-3 tasks. If the pending entry already had a
   `phase`/`phaseTitle`, use those instead of proposing new ones. Don't
   generate `<DiagramFigure>` SVGs — skip diagrams entirely, they need a
   human review pass.

4. Write that JSON to a temp file and apply it:
   ```bash
   scripts/lesson-pipeline/.venv/bin/python3 scripts/lesson-pipeline/apply_lesson.py \
     --config <config-path> --url "<the url from step 1>" --data <path-to-your-json>
   ```
   This computes `order`/`lessonNumber` from what's already in
   `apps/<topic>`, writes the `.mdx` file, and marks the URL `processed`
   in the config. If it errors (topic has no matching `apps/<topic>` dir,
   URL already processed, malformed JSON), fix and retry rather than
   editing the config by hand.

## Mode B steps (external LLM, on request)

1. Read the config's `llm.provider` (or `LESSON_LLM_PROVIDER` env var).
   For `anthropic`/`openai`, confirm the relevant API key env var
   (`llm.api_key_env`, default `ANTHROPIC_API_KEY`) is set; for `local`,
   confirm `llm.base_url` is set. If missing, tell the user which one and
   stop — don't guess a placeholder value.
2. Run:
   ```bash
   scripts/lesson-pipeline/.venv/bin/python3 scripts/lesson-pipeline/generate_lesson.py --config <config-path>
   ```
3. Surface any error verbatim (missing key, fetch failure, LLM response
   that didn't parse as the expected JSON, etc.) — it's already written
   to be actionable.

## Both modes

**Report the result** back to the user in a few lines: which URL was
processed, which topic/app it went into, and the exact path of the
generated `.mdx` file.

**Do not commit, deploy, or run this in a loop.** This drafts one lesson
per invocation; it does not publish anything. Leave the new file and the
updated config for the user to read, sanity-check with
`pnpm build:<topic>`, and commit themselves. If the user wants the next
URL processed too, they'll invoke `/add-lesson` again.
