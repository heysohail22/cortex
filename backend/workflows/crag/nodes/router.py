from __future__ import annotations

import asyncio
import logging
from typing import cast

import config
from workflows.crag.state import CRAGState

logger = logging.getLogger(__name__)

from services.routing import classify_async


async def router_node(state: CRAGState) -> CRAGState:
    classification = await classify_async(
        question=state["question"], has_documents=state["has_documents"],
        documents=state.get("document_profiles") or state.get("document_names", []),
        conversation_history=state.get("conversation_history", ""),
    )
    route = classification["route"]
    terminal = route in ("unsafe", "unavailable", "clarify")
    return {
        **state, "route": route, "router_decision": classification,
        "answer": classification.get("direct_answer", "") if terminal else "",
        "source": "guardrail" if terminal else "",
        "is_grounded": False if terminal else state.get("is_grounded", False),
    }
