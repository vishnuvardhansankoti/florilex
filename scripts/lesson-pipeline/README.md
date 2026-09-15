# Lesson-generation pipeline

Takes the next unprocessed URL from a config file, researches it, writes
an original lesson based on it, and saves the result as a new `.mdx` file
in the right `apps/<topic>/src/content/lessons/phases/...` directory —
matching the schema in that app's `src/content/config.ts`. Then marks the
URL processed so the next run picks up the following one.

There are two ways to do the research-and-write step:

- **`/add-lesson` in Claude Code (recommended for local use)** — Claude
  Code itself fetches and researches the page (its own `WebFetch`/
  `WebSearch` tools) and writes the lesson, running on your existing
  Claude subscription. No Anthropic/OpenAI API key needed. Under the
  hood it uses `next_pending.py` to read the queue and `apply_lesson.py`
  to place the file and mark it processed — neither makes an LLM call.
- **`generate_lesson.py` (for automation without a live Claude session)**
  — calls a config-driven external LLM (Anthropic/OpenAI API key, or a
  local/Ollama model) to do the research and writing non-interactively.
  Useful for a cron job or CI, or if you specifically want a different
  model. This is the only path that costs metered API usage.

This directory is self-contained: its own package (`lesson_pipeline/`),
its own deps (`requirements.txt`), its own venv (`.venv/`, gitignored).
`scripts/deploy/deploy-firebase.sh` is unrelated repo-wide tooling.

## Setup

Run from the repo root:

```bash
uv venv scripts/lesson-pipeline/.venv
uv pip install --python scripts/lesson-pipeline/.venv/bin/python3 -r scripts/lesson-pipeline/requirements.txt
cp scripts/lesson-pipeline/lesson-sources.example.yaml scripts/lesson-pipeline/lesson-sources.yaml
# edit lesson-sources.yaml: add real URLs

# only needed for generate_lesson.py (external LLM) — /add-lesson needs neither:
export ANTHROPIC_API_KEY=...   # or whatever llm.api_key_env names
```

No `uv`? Same result with stdlib tools:
```bash
python3 -m venv scripts/lesson-pipeline/.venv
scripts/lesson-pipeline/.venv/bin/pip install -r scripts/lesson-pipeline/requirements.txt
```

Deliberately an isolated venv rather than a global install —
`anthropic`/`openai` pull in `httpx`/`aiohttp`-adjacent deps that can
conflict with unrelated tools already in a shared environment. This bit
us once: installing these globally required upgrading `aiohttp` to
satisfy `openai`'s vendored transport, which risked breaking `streamlit`
elsewhere in that same environment. A clean venv (especially one built
with `uv`, which never touches anything outside the venv it creates)
sidesteps this entirely — `openai`'s `aiohttp`-based fallback path isn't
even exercised when no stray `aiohttp` is lying around to be picked up.

`lesson-sources.yaml` is gitignored — it's your personal reading queue
and its processed-status history, not repo content.

## Run

Recommended: in Claude Code, run `/add-lesson` (see
`.claude/skills/add-lesson/`). It reads the queue with `next_pending.py`,
does the research and writing itself, and files the result with
`apply_lesson.py` — all under your Claude subscription, no API key.

To use an external LLM instead (Mode B — needs an API key or a local
model):
```bash
scripts/lesson-pipeline/.venv/bin/python3 scripts/lesson-pipeline/generate_lesson.py --config scripts/lesson-pipeline/lesson-sources.yaml
# or, equivalently (defaults to lesson-sources.yaml in this directory):
scripts/lesson-pipeline/grill-me.sh

# generate without marking the URL as processed (e.g. to inspect output first):
scripts/lesson-pipeline/.venv/bin/python3 scripts/lesson-pipeline/generate_lesson.py --config scripts/lesson-pipeline/lesson-sources.yaml --dry-run
```

Each run (either mode) processes exactly one URL — the first entry whose
`status` isn't `processed`. Re-run to work through the rest of the list.

## Config schema (YAML / JSON)

```yaml
llm:
  provider: anthropic       # anthropic | openai | local
  model: claude-sonnet-5
  api_key_env: ANTHROPIC_API_KEY   # ignored for provider: local
  base_url: null                    # required for provider: local, e.g. http://localhost:11434
  local_api_style: ollama           # ollama | openai (provider: local only)
  enable_web_search: true           # server-side web search — anthropic/openai only
  max_tokens: 8000
  web_search_tool: null             # override the tool spec sent to Anthropic if the API version drifts

urls:
  - url: "https://example.com/article"
    topic: aiml            # must match a directory under apps/ (aiml, go, ...)
    status: pending         # anything other than processed/done/complete counts as pending
    phase: "02-attention"        # optional — omit to let the LLM propose one
    phaseTitle: "Phase 02 — Attention"   # optional, paired with `phase`
```

CSV works too (`url,topic,status,phase,phaseTitle` columns — see
`lesson-sources.example.csv`), but CSV has no room for the `llm:` block, so
LLM settings must come from env vars (`LESSON_LLM_PROVIDER`,
`LESSON_LLM_MODEL`, `LESSON_LLM_BASE_URL`) when using a CSV config.

`order` and `lessonNumber` are always computed automatically from what's
already in `apps/<topic>` (global increment for `order`, per-phase count
for `lessonNumber`) — they aren't configurable per entry, to avoid
collisions.

## What gets generated

The LLM is asked for one JSON object (title, subtitle, summary, hook,
phase, a list of sections, a list of tasks) which is rendered into MDX
using the same structure existing lessons use: `<section class="lesson">`
blocks with numbered headings, and `<WorkTask>`/`<Solution>` pairs. It may
use `<Callout>` and `<Formula>` inline; it's not asked to generate
`<DiagramFigure>` SVGs, since those are hard to get right without a human
review pass.

Always review and `pnpm build:<topic>` the generated lesson before
committing — this pipeline drafts, it doesn't publish unattended.
