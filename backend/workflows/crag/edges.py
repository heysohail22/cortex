"""
CRAG Edges — Conditional routing and branching logic for Corrective RAG with hard loop bounds.
"""
from __future__ import annotations

import logging
from typing import Literal

from workflows.crag.state import CRAGState

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


def decide_after_retrieval_eval(state: CRAGState) -> str:
    status = state.get("evidence_status", "UNKNOWN")
    if status == "SUFFICIENT":
        return "generate_node"
    if status in ("PARTIAL", "NONE") and state.get("retrieval_corrections_used", 0) < 1:
        return "retrieval_correction_node"
    return "evidence_finalize_node"


def decide_after_correction(state: CRAGState) -> str:
    return "retrieve_node" if state.get("correction_action") == "retrieve" else "evidence_finalize_node"


def decide_after_evidence_finalize(state: CRAGState) -> str:
    return {"generate": "generate_node", "web": "supplemental_web_node"}.get(state.get("finalize_action"), "END")


def decide_after_supplement(state: CRAGState) -> str:
    if state.get("evidence_status") != "UNKNOWN" and state.get("finalize_action") == "generate":
        return "generate_node"
    return "evidence_finalize_node"


def decide_after_groundedness(
    state: CRAGState
) -> Literal["strict_retry_node", "safe_fallback_node", "END"]:
    """
    NLI Groundedness Check with Strict Loop Bounds:
    - Entailment (Grounded >= 0.85): Terminate to END / Output Guard.
    - Contradiction / Neutral (Attempt 1, retry_count < 1): Route to Strict Constrained Generator.
    - Contradiction / Neutral (Retry Exhausted, retry_count >= 1): Route to Safe Refusal & Verbatim Fallback.
    """
    if state.get("nli_verdict") == "NOT_CHECKED":
        return "END"
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
