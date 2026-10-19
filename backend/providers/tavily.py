from __future__ import annotations

import asyncio
import logging
import re
from typing import Dict, List
from tavily import TavilyClient
import config

logger = logging.getLogger(__name__)


def _clean_web_results(raw_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extracts only clean, relevant fields from Tavily search results, discarding raw scrapes."""
    clean_results = []
    seen_urls = set()

    for r in raw_results:
        url = str(r.get("url", "")).strip()
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)

        title = str(r.get("title", "No Title")).strip()
        content = str(r.get("content", "")).strip()
        # Normalize whitespace (collapse multiple newlines/tabs/spaces)
        content = re.sub(r"\s+", " ", content)

        if not content:
            continue

        clean_results.append({
            "title": title,
            "url": url,
            "content": content,
            "score": float(r.get("score", 0.0)) if r.get("score") is not None else 0.0,
        })

    return clean_results


async def search_web_async(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Asynchronously executes a web search using Tavily without blocking the event loop.
    Extracts and sanitizes only relevant clean text fields, discarding raw HTML payloads.
    """
    client = TavilyClient(api_key=config.TAVILY_API_KEY)

    try:
        response = await asyncio.to_thread(
            client.search,
            query=query,
            search_depth="basic",
            max_results=max_results,
        )
        raw_results = response.get("results", [])
        return _clean_web_results(raw_results)
    except Exception as e:
        logger.error("Tavily search error for query '%s': %s", query, e)
        return []
