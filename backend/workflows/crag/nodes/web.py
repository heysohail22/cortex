from __future__ import annotations

import asyncio
import logging
from typing import cast

import config
from workflows.crag.state import CRAGState

logger = logging.getLogger(__name__)

from services.query_rewriting import rewrite_query_for_web_async
from providers.tavily import search_web_async


async def web_search_node(state: CRAGState) -> CRAGState:
    query = state.get("transformed_query") or state["question"]
    try:
        results = await asyncio.wait_for(
            search_web_async(query, max_results=5),
            timeout=config.TIMEOUT_WEB_SEARCH,
        )
    except asyncio.TimeoutError:
        logger.warning("Tavily web search timed out after %.1fs. Continuing with empty web results.", config.TIMEOUT_WEB_SEARCH)
        results = []
    except Exception as e:
        logger.warning("Web search error: %s. Continuing with empty web results.", e)
        results = []

    return {**state, "web_results": results}


async def direct_web_search_node(state: CRAGState) -> CRAGState:
    """Fetches live news and current events from Tavily, feeding results to Generator Node."""
    active_query = state.get("transformed_query") or state["question"]
    try:
        query = await asyncio.wait_for(
            rewrite_query_for_web_async(active_query),
            timeout=config.TIMEOUT_ROUTER,
        )
        results = await asyncio.wait_for(
            search_web_async(query, max_results=5),
            timeout=config.TIMEOUT_WEB_SEARCH,
        )
    except Exception as e:
        logger.warning("Direct web search error: %s", e)
        query = active_query
        results = []

    return cast(
        CRAGState,
        {
            **state,
            "transformed_query": query,
            "web_results": results,
            "evaluation_result": "INCORRECT",  # Indicates web-sourced generation for generator node
        },
    )
