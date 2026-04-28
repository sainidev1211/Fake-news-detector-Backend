"""
services/verification.py — Wikipedia-based external verification layer.

Flow:
  1. Extract top keywords from the content (frequency-based, no NLTK needed).
  2. Query Wikipedia REST API for each keyword.
  3. Return the first useful summary as context for the LLM.
"""
import asyncio
import re
from typing import Optional
import httpx
from utils.logger import get_logger

logger = get_logger("verification")

_WIKI_API = "https://en.wikipedia.org/api/rest_v1/page/summary/{}"
_STOP_WORDS = {
    "the","a","an","and","or","but","in","on","at","to","for","of","with",
    "is","was","are","were","be","been","being","have","has","had","do","does",
    "did","will","would","could","should","may","might","shall","can","this",
    "that","these","those","it","its","as","by","from","up","about","into",
    "through","during","before","after","above","below","between","each",
    "few","more","most","other","some","such","no","not","only","own","same",
    "so","than","too","very","just","because","while","although","however",
    "says","said","according","new","also","their","they","he","she","we",
    "you","i","us","him","her","them","our","your","his","her","who","which",
    "what","when","where","how","why","all","both","any","much","many",
}


def _extract_keywords(text: str, top_n: int = 4) -> list[str]:
    """Return the top-N meaningful words by frequency."""
    words = re.findall(r"[a-zA-Z]{4,}", text.lower())
    freq: dict[str, int] = {}
    for w in words:
        if w not in _STOP_WORDS:
            freq[w] = freq.get(w, 0) + 1
    return sorted(freq, key=lambda k: -freq[k])[:top_n]


async def _fetch_wiki_summary(keyword: str, client: httpx.AsyncClient) -> Optional[str]:
    """Fetch a Wikipedia page summary for a single keyword."""
    try:
        url = _WIKI_API.format(keyword.replace(" ", "_"))
        resp = await client.get(url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            extract = data.get("extract", "")
            if extract and len(extract) > 80:
                title = data.get("title", keyword)
                return f"[Wikipedia – {title}]: {extract[:500]}"
    except Exception as exc:
        logger.debug("Wikipedia fetch failed for '%s': %s", keyword, exc)
    return None


async def get_wikipedia_context(text: str) -> Optional[str]:
    """
    Given article text, return a Wikipedia-derived context string
    (or None if nothing useful is found).
    """
    keywords = _extract_keywords(text)
    if not keywords:
        return None

    logger.info("Querying Wikipedia for keywords: %s", keywords)
    async with httpx.AsyncClient() as client:
        tasks = [_fetch_wiki_summary(kw, client) for kw in keywords]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    for r in results:
        if isinstance(r, str) and r:
            return r          # return first successful hit

    return None
