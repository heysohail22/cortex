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
    """Only a failed support check can use the single answer repair allowance."""
    status = state.get("verification_status", "UNKNOWN")
    if status in ("SUPPORTED", "SKIPPED"):
        return "END"
    if status == "UNSUPPORTED" and state.get("answer_repairs_used", 0) < 1:
        return "strict_retry_node"
    return "safe_fallback_node"
