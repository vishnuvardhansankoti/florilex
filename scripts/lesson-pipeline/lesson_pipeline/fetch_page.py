"""Fetch a URL and extract its title + readable text for the LLM prompt."""

from __future__ import annotations

import requests
from bs4 import BeautifulSoup

USER_AGENT = "florilex-lesson-pipeline/1.0"


def fetch_page(url: str, timeout: int = 20) -> tuple[str, str]:
    response = requests.get(url, timeout=timeout, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    title = soup.title.string.strip() if soup.title and soup.title.string else url

    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "svg"]):
        tag.decompose()

    text = soup.get_text("\n", strip=True)
    return title, text
