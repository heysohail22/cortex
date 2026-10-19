"""
CRAG Edges — Conditional routing and branching logic for Corrective RAG with hard loop bounds.
"""
from __future__ import annotations

import logging
from typing import Literal

from crag.state import CRAGState

logger = logging.getLogger(__name__)


def decide_route(state: CRAGState) -> Literal["retrieve_node", "direct_web_search_node", "direct_answer_node", "END"]:
    """Routes initial user intent from the Router Node."""
    route = state.get("route", "direct_answer")
    if route == "rag":
        return "retrieve_node"
    if route == "web_search":
        return "direct_web_search_node"
    if route == "direct_answer":
        return "direct_answer_node"
    # Safety, clarification and unavailable decisions terminate without generation.
    return "END"


def decide_after_retrieval_eval(
    state: CRAGState
) -> Literal[
    "generate_node",
    "retrieve_node",
    "web_search_node",
]:
    """
    CRAG Direct Branching with Strict Loop Bounds:
    - CORRECT: Chunks are relevant -> Proceed directly to generate_node.
    - INCORRECT (1st attempt, db_retry_count <= 1): Loops back to retrieve_node with bundled db query.
    - INCORRECT (2nd attempt / max retries reached): Vector DB exhausted -> Proceeds directly to web_search_node.
    - AMBIGUOUS: Proceeds directly to web_search_node for hybrid augmentation.
    """
    evaluation = state.get("evaluation_result", "CORRECT")
    db_retry_count = state.get("db_retry_count", 0)

    if evaluation == "CORRECT":
        return "generate_node"

    if evaluation == "INCORRECT":
        # Strict hard loop bound: Allow at most 1 retry to prevent infinite retrieval cycles
        if db_retry_count <= 1:
            logger.info(
                "CRAG Eval: Chunks INCORRECT on 1st retrieval (retry %d/1). Looping back to retrieve_node...",
                db_retry_count,
            )
            return "retrieve_node"
        logger.info(
            "CRAG Eval: Chunks STILL INCORRECT after max retries (%d). Proceeding to web_search_node...",
            db_retry_count,
        )
        return "web_search_node"

    # AMBIGUOUS path
    logger.info("CRAG Eval: Retrieval is AMBIGUOUS. Proceeding to web_search_node for hybrid augmentation...")
    return "web_search_node"


def decide_after_groundedness(
    state: CRAGState
) -> Literal["strict_retry_node", "safe_fallback_node", "END"]:
    """
    NLI Groundedness Check with Strict Loop Bounds:
    - Entailment (Grounded >= 0.85): Terminate to END / Output Guard.
    - Contradiction / Neutral (Attempt 1, retry_count < 1): Route to Strict Constrained Generator.
    - Contradiction / Neutral (Retry Exhausted, retry_count >= 1): Route to Safe Refusal & Verbatim Fallback.
    """
    is_grounded = state.get("is_grounded", True)
    retry_count = state.get("groundedness_retry_count", 0)

    if is_grounded:
        return "END"

    if retry_count < 1:
        logger.warning(
            "NLI Groundedness Judge detected hallucination/contradiction (retry %d/1). Routing to Strict Constrained Generator...",
            retry_count,
        )
        return "strict_retry_node"

    logger.warning("NLI Groundedness retry limit reached (%d). Routing to Safe Refusal Fallback...", retry_count)
    return "safe_fallback_node"
