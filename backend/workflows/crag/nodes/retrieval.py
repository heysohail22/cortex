"""Bounded retrieval correction and explicit terminal evidence outcomes."""
from __future__ import annotations

import asyncio

import config
from workflows.crag.state import CRAGState
from retrieval import vector_store as vs
from services.evidence import LEGACY_LABEL, evaluate_retrieval_async
from retrieval.evidence import merge_candidates
from services.query_rewriting import rewrite_retrieval_query_async
from providers.tavily import search_web_async


def _unknown(state: CRAGState, reason: str) -> dict:
    return {**state, "evidence_status": "UNKNOWN", "evaluation_result": "UNKNOWN",
            "evaluation_reason": reason, "chunks": [], "refined_chunks": [], "retained_evidence": []}


async def retrieve_node(state: CRAGState) -> CRAGState:
    try:
        chunks = await asyncio.to_thread(
            vs.similarity_search, state["session_id"], state.get("transformed_query") or state["question"], k=config.TOP_K_RESULTS,
        )
        return {**state, "chunks": chunks, "retrieval_status": "ok"}
    except Exception:
        return {**_unknown(state, "Document retrieval is temporarily unavailable."), "retrieval_status": "error"}


async def retrieval_eval_node(state: CRAGState) -> CRAGState:
    if state.get("retrieval_status") == "error":
        return _unknown(state, "Document retrieval is temporarily unavailable.")
    try:
        candidates = merge_candidates(state.get("retained_evidence", []) + state.get("chunks", []))
        result = await evaluate_retrieval_async(
            state["question"], candidates, state.get("document_names", []), state.get("conversation_history", ""),
        )
        return {**state, "chunks": result.chunks, "refined_chunks": result.chunks,
                "retained_evidence": result.chunks, "evidence_status": result.status,
                "evaluation_result": LEGACY_LABEL[result.status], "evaluation_reason": result.reason,
                "evidence_assessment": result.metadata, "conflicting_ids": result.conflicting_ids,
                "missing_requirements": "" if result.status == "SUFFICIENT" else state.get("missing_requirements", "")}
    except Exception:
        return _unknown(state, "Evidence assessment is temporarily unavailable.")


def _normalized(query: str) -> str:
    return " ".join("".join(char.lower() if char.isalnum() else " " for char in query).split())


async def retrieval_correction_node(state: CRAGState) -> CRAGState:
    if state.get("retrieval_corrections_used", 0) >= 1:
        return {**state, "correction_action": "finalize"}
    try:
        rewrite = await rewrite_retrieval_query_async(
            state["question"], state.get("retained_evidence", []), state["evidence_status"],
            state.get("conversation_history", ""),
        )
    except Exception:
        return {**state, "correction_action": "finalize"}
    missing = rewrite.missing_requirements.strip()
    clarification = rewrite.clarification.strip()
    query = rewrite.query.strip()
    if clarification:
        return {**state, "missing_requirements": missing, "clarification": clarification, "correction_action": "finalize"}
    if not query or _normalized(query) == _normalized(state.get("transformed_query") or state["question"]):
        return {**state, "missing_requirements": missing, "correction_action": "finalize"}
    return {**state, "transformed_query": query, "db_rewritten_query": query,
            "missing_requirements": missing, "retrieval_corrections_used": 1, "db_retry_count": 1,
            "correction_action": "retrieve"}


def terminal_response(state: CRAGState, answer: str, route: str) -> CRAGState:
    return {**state, "finalize_action": "", "answer": answer, "route": route, "source": "guardrail", "citations": [],
            "is_grounded": None, "verification_status": "SKIPPED", "nli_verdict": "NOT_CHECKED", "nli_score": None,
            "groundedness_reason": "No factual answer was verified."}


async def evidence_finalize_node(state: CRAGState) -> CRAGState:
    if state.get("evidence_status") == "UNKNOWN":
        return terminal_response(state, "I could not retrieve or assess document evidence right now. Please try again shortly.", "retrieval_unavailable")
    if state.get("clarification"):
        return terminal_response(state, state["clarification"], "clarify")
    # Only trusted server callers can supply this policy and independently approved query.
    # No query is ever derived from private passages, a model decision or conversation.
    if (state.get("external_evidence_policy") == "public_supplement" and state.get("approved_public_query")
            and not state.get("external_search_used")):
        return {**state, "finalize_action": "web"}
    if state.get("retained_evidence"):
        return {**state, "finalize_action": "generate", "chunks": state["retained_evidence"]}
    return terminal_response(state, "I could not find supporting evidence in the retrieved document passages. Please provide the relevant document or clarify your question.", "no_document_evidence")


async def supplemental_web_node(state: CRAGState) -> CRAGState:
    state = {**state, "external_search_used": True, "finalize_action": ""}
    if state.get("external_evidence_policy") != "public_supplement" or not state.get("approved_public_query"):
        return _unknown(state, "External evidence was not authorized.")
    try:
        # A trusted caller must approve the public query independently of private context.
        from guardrails import redact_pii_async
        query = (await redact_pii_async(state["approved_public_query"])).sanitized_text
        results = await search_web_async(query, max_results=5)
        web_chunks = [{"source": r["url"], "text": r.get("content", "")} for r in results if r.get("url")]
        # No private context is sent to Tavily. Jev assesses public snippets against the question.
        assessment = await evaluate_retrieval_async(state["question"], web_chunks)
        if assessment.status == "UNKNOWN":
            return _unknown(state, "External evidence assessment unavailable.")
        safe = {c["source"]: c["text"] for c in assessment.chunks}
        selected = [{**r, "content": safe[r["url"]]} for r in results if r.get("url") in safe]
        return {**state, "web_results": selected, "external_evidence_status": assessment.status,
                "finalize_action": "generate" if selected or state.get("retained_evidence") else "finalize"}
    except Exception:
        return {**state, "web_results": [], "finalize_action": "generate" if state.get("retained_evidence") else "finalize"}
