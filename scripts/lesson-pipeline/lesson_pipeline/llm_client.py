"""Config-driven LLM client: cloud (Anthropic/OpenAI, with server-side web
search) or local (an Ollama-compatible endpoint, no web search).

Every provider is asked for the exact same thing: a single fenced ```json
block matching the schema in PROMPT_TEMPLATE, which lesson_writer.py then
turns directly into an .mdx file.
"""

from __future__ import annotations

import json
import os
import re

# Config-driven so a stale tool-version string here doesn't require a code
# change — override via llm.web_search_tool in the config file if Anthropic
# revs this.
DEFAULT_ANTHROPIC_WEB_SEARCH_TOOL = {
    "type": "web_search_20250305",
    "name": "web_search",
    "max_uses": 5,
}
DEFAULT_OPENAI_WEB_SEARCH_TOOL = {"type": "web_search_preview"}

PROMPT_TEMPLATE = """You are writing a tutorial lesson for the "{topic}" series of Florilex, \
a from-scratch technical tutorial site. The house style teaches concepts from first \
principles with worked examples, not a reformatting of the source article.

Source article:
URL: {url}
Title: {page_title}

Article text (may be partial or noisy — it was scraped):
\"\"\"
{page_text}
\"\"\"

Do the following:
1. If you have web search available, use it sparingly to check facts, fill gaps the \
article doesn't cover, or confirm the material is current.
2. Write an original lesson elaborating on and teaching the underlying ideas — do not \
just summarize or paraphrase the article.
3. Respond with ONLY a single fenced ```json code block, no other text, containing an \
object with exactly this shape:

```json
{{
  "title": "lesson title, inline <em>...</em> allowed for emphasis",
  "subtitle": "one-sentence subtitle, inline HTML allowed",
  "summary": "2-4 sentence plain-text summary, no HTML tags",
  "hook": "optional short punchy pull-quote, or null",
  "hookCredit": "optional attribution for the hook, or null",
  "phaseTitle": "human phase title, e.g. 'Phase 02 — Attention'",
  "phaseSlug": "kebab-case slug matching phaseTitle, e.g. '02-attention'",
  "lessonSlug": "kebab-case slug for this lesson, no number prefix, e.g. 'self-attention-from-scratch'",
  "sections": [
    {{
      "heading": "Section heading",
      "body_md": "one or more paragraphs of markdown. You may inline at most one <Callout label=\\"...\\"> ... </Callout> or <Formula name=\\"...\\"> ... </Formula> block per section, only if genuinely useful."
    }}
  ],
  "tasks": [
    {{
      "label": "Task 1 · Implement",
      "title": "short task title",
      "prompt_md": "markdown task prompt",
      "solution_md": "markdown solution, fenced code blocks allowed"
    }}
  ]
}}
```

Write 3-6 sections and 1-3 tasks. Keep body_md/prompt_md/solution_md as valid \
Markdown/MDX — no raw HTML besides the two components mentioned above."""


class LLMError(RuntimeError):
    pass


def resolve_llm_config(llm_cfg: dict) -> dict:
    """Merges the config file's `llm:` block with env var overrides and defaults."""
    provider = os.environ.get("LESSON_LLM_PROVIDER", llm_cfg.get("provider", "anthropic"))
    return {
        "provider": provider,
        "model": os.environ.get("LESSON_LLM_MODEL", llm_cfg.get("model", "claude-sonnet-5")),
        "api_key_env": llm_cfg.get("api_key_env", "ANTHROPIC_API_KEY"),
        "base_url": os.environ.get("LESSON_LLM_BASE_URL", llm_cfg.get("base_url")),
        "local_api_style": llm_cfg.get("local_api_style", "ollama"),
        "enable_web_search": bool(llm_cfg.get("enable_web_search", True)),
        "max_tokens": int(llm_cfg.get("max_tokens", 8000)),
        "web_search_tool": llm_cfg.get("web_search_tool", DEFAULT_ANTHROPIC_WEB_SEARCH_TOOL),
    }


def _call_anthropic(cfg: dict, prompt: str) -> str:
    try:
        import anthropic
    except ImportError as e:
        raise LLMError("provider 'anthropic' needs: pip install anthropic") from e

    api_key = os.environ.get(cfg["api_key_env"])
    if not api_key:
        raise LLMError(f"Missing API key: set env var {cfg['api_key_env']}")

    client = anthropic.Anthropic(api_key=api_key)
    tools = [cfg["web_search_tool"]] if cfg["enable_web_search"] else []
    response = client.messages.create(
        model=cfg["model"],
        max_tokens=cfg["max_tokens"],
        tools=tools,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(block.text for block in response.content if getattr(block, "type", None) == "text")


def _call_openai(cfg: dict, prompt: str) -> str:
    try:
        import openai
    except ImportError as e:
        raise LLMError("provider 'openai' needs: pip install openai") from e

    api_key = os.environ.get(cfg["api_key_env"])
    if not api_key:
        raise LLMError(f"Missing API key: set env var {cfg['api_key_env']}")

    client = openai.OpenAI(api_key=api_key, base_url=cfg["base_url"] or None)
    tools = [DEFAULT_OPENAI_WEB_SEARCH_TOOL] if cfg["enable_web_search"] else []
    response = client.responses.create(
        model=cfg["model"],
        input=prompt,
        tools=tools,
        max_output_tokens=cfg["max_tokens"],
    )
    return response.output_text


def _call_local(cfg: dict, prompt: str) -> str:
    base_url = cfg["base_url"]
    if not base_url:
        raise LLMError("provider 'local' needs llm.base_url set (e.g. http://localhost:11434)")

    if cfg["local_api_style"] == "openai":
        try:
            import openai
        except ImportError as e:
            raise LLMError("local_api_style 'openai' needs: pip install openai") from e
        api_key = os.environ.get(cfg["api_key_env"], "local") if cfg.get("api_key_env") else "local"
        client = openai.OpenAI(api_key=api_key, base_url=base_url)
        response = client.chat.completions.create(
            model=cfg["model"],
            messages=[{"role": "user", "content": prompt}],
            max_tokens=cfg["max_tokens"],
        )
        return response.choices[0].message.content

    # Default: Ollama's native /api/chat.
    import requests

    resp = requests.post(
        f"{base_url.rstrip('/')}/api/chat",
        json={
            "model": cfg["model"],
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "options": {"num_predict": cfg["max_tokens"]},
        },
        timeout=900,
    )
    resp.raise_for_status()
    return resp.json()["message"]["content"]


def _parse_json_block(text: str) -> dict:
    match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    raw = match.group(1) if match else text
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise LLMError(f"Could not parse JSON from LLM response:\n\n{text}") from e


def elaborate_and_summarize(llm_cfg: dict, *, topic: str, url: str, page_title: str, page_text: str) -> dict:
    prompt = PROMPT_TEMPLATE.format(
        topic=topic,
        url=url,
        page_title=page_title,
        page_text=page_text[:15000],
    )

    provider = llm_cfg["provider"]
    if provider == "anthropic":
        text = _call_anthropic(llm_cfg, prompt)
    elif provider == "openai":
        text = _call_openai(llm_cfg, prompt)
    elif provider == "local":
        text = _call_local(llm_cfg, prompt)
    else:
        raise LLMError(f"Unknown llm.provider: {provider!r} (use anthropic, openai, or local)")

    return _parse_json_block(text)
