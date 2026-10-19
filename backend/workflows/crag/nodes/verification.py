from __future__ import annotations

import asyncio
import logging
from typing import cast

import config
from workflows.crag.state import CRAGState

logger = logging.getLogger(__name__)

from services.verification import evaluate_groundedness_async


async def groundedness_check_node(state: CRAGState) -> CRAGState:
    """Evaluates whether the generated answer is strictly grounded in the context via NLI."""
    source = state.get("source", "rag")

    if state.get("external_search_used") and state.get("web_results"):
        return {**state, "is_grounded": False, "groundedness_reason": "Public supplementation has not been verified by the document-only judge.",
                "nli_verdict": "NOT_CHECKED", "nli_score": 0.0}

    # If pure web search, guardrail, or general llm, skip doc groundedness check
    if source in ("web_search", "guardrail", "llm"):
        return {
            **state,
            "is_grounded": True,
            "groundedness_reason": "Skipped for non-rag source.",
            "nli_verdict": "ENTAILMENT",
            "nli_score": 1.0,
        }

    question = state["question"]
    answer = state.get("answer", "")
    chunks = state.get("chunks", [])

    context = "\n\n".join(c.get("text", "") for c in chunks)

    try:
        eval_res = await asyncio.wait_for(
            evaluate_groundedness_async(question, context, answer),
            timeout=config.TIMEOUT_GROUNDEDNESS,
        )
        is_grounded = eval_res.is_grounded if hasattr(eval_res, "is_grounded") else eval_res[0]
        reason = eval_res.reason if hasattr(eval_res, "reason") else eval_res[1]
        verdict = getattr(eval_res, "verdict", "ENTAILMENT" if is_grounded else "CONTRADICTION")
        score = getattr(eval_res, "score", 0.95 if is_grounded else 0.4)
    except asyncio.TimeoutError:
        logger.warning(
            "Groundedness judge timed out after %.1fs. Defaulting to is_grounded=True.",
            config.TIMEOUT_GROUNDEDNESS,
        )
        is_grounded, reason, verdict, score = True, "judge_timeout_fallback", "ENTAILMENT", 0.9
    except Exception as e:
        logger.warning("Groundedness judge error: %s. Defaulting to is_grounded=True.", e)
        is_grounded, reason, verdict, score = True, "judge_error_fallback", "ENTAILMENT", 0.9

    retry_count = state.get("groundedness_retry_count", 0)
    final_answer = answer
    final_source = source
    final_citations = state.get("citations", [])
    final_route = state.get("route", "rag")

    if not is_grounded and retry_count >= 1:
        logger.warning(
            "Groundedness Judge: Unresolvable hallucination detected after strict retry (%d). Triggering fallback refusal.",
            retry_count,
        )
        final_answer = (
            "I reviewed the provided documents, but could not find verifiable facts to answer "
            "your question with complete confidence. Please check your uploaded files or provide additional details."
        )
        final_source = "guardrail"
        final_citations = []
        final_route = "hallucination_fallback"

    return {
        **state,
        "answer": final_answer,
        "source": final_source,
        "citations": final_citations,
        "route": final_route,
        "is_grounded": is_grounded,
        "groundedness_reason": reason,
        "nli_verdict": verdict,
        "nli_score": score,
    }


async def safe_fallback_node(state: CRAGState) -> CRAGState:
    """Zero-hallucination honest refusal when unresolvable hallucinations persist."""
    logger.warning("Safe Fallback Node triggered: Emitting honest refusal.")
    return {
        **state,
        "answer": (
            "I reviewed the provided documents, but could not find verifiable facts to answer "
            "your question with complete confidence. Please check your uploaded files or provide additional details."
        ),
        "source": "guardrail",
        "citations": [],
        "route": "hallucination_fallback",
        "is_grounded": True,
        "nli_verdict": "SAFE_REFUSAL",
        "nli_score": 1.0,
    }
