"""
CRAG Graph — Compiles the StateGraph workflow for Corrective RAG.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict

from langgraph.graph import StateGraph, END

from workflows.crag.state import CRAGState
from workflows.crag import nodes, edges
from repositories import documents as vs

logger = logging.getLogger(__name__)


def _build_crag_graph() -> Any:
    graph = StateGraph(CRAGState)

    # 1. Add CRAG Core Nodes
    graph.add_node("router", nodes.router_node)
    graph.add_node("direct_answer_node", nodes.direct_answer_node)
    graph.add_node("retrieve_node", nodes.retrieve_node)
    graph.add_node("retrieval_eval_node", nodes.retrieval_eval_node)
    graph.add_node("retrieval_correction_node", nodes.retrieval_correction_node)
    graph.add_node("evidence_finalize_node", nodes.evidence_finalize_node)
    graph.add_node("supplemental_web_node", nodes.supplemental_web_node)
    graph.add_node("web_search_node", nodes.web_search_node)
    graph.add_node("generate_node", nodes.generate_node)
    graph.add_node("groundedness_check_node", nodes.groundedness_check_node)
    graph.add_node("strict_retry_node", nodes.strict_constrained_generator_node)
    graph.add_node("safe_fallback_node", nodes.safe_fallback_node)
    graph.add_node("direct_web_search_node", nodes.direct_web_search_node)

    # 2. Set Entry Point: Directly to Intent Router
    graph.set_entry_point("router")

    # 3. Router Conditional Edges
    graph.add_conditional_edges(
        "router",
        edges.decide_route,
        {
            "direct_answer_node": "direct_answer_node",
            "retrieve_node": "retrieve_node",
            "direct_web_search_node": "direct_web_search_node",
            "END": END,
        },
    )

    graph.add_edge("direct_answer_node", END)

    # Direct Web Search feeds into Context-Budgeted Generator Node
    graph.add_edge("direct_web_search_node", "generate_node")

    # 4. CRAG Core Pipeline Edges
    graph.add_edge("retrieve_node", "retrieval_eval_node")
    graph.add_conditional_edges(
        "retrieval_eval_node",
        edges.decide_after_retrieval_eval,
        {
            "generate_node": "generate_node",
            "retrieval_correction_node": "retrieval_correction_node",
            "evidence_finalize_node": "evidence_finalize_node",
        },
    )

    graph.add_conditional_edges("retrieval_correction_node", edges.decide_after_correction,
        {"retrieve_node": "retrieve_node", "evidence_finalize_node": "evidence_finalize_node"})
    graph.add_conditional_edges("evidence_finalize_node", edges.decide_after_evidence_finalize,
        {"generate_node": "generate_node", "supplemental_web_node": "supplemental_web_node", "END": END})
    graph.add_conditional_edges("supplemental_web_node", edges.decide_after_supplement,
        {"generate_node": "generate_node", "evidence_finalize_node": "evidence_finalize_node"})

    # Legacy web node retained for compatibility; retrieval does not automatically enter it.
    graph.add_edge("web_search_node", "generate_node")

    # 5. Generation -> NLI Groundedness Fact-Check Judge
    graph.add_edge("generate_node", "groundedness_check_node")
    graph.add_conditional_edges(
        "groundedness_check_node",
        edges.decide_after_groundedness,
        {
            "strict_retry_node": "strict_retry_node",
            "safe_fallback_node": "safe_fallback_node",
            "END": END,
        },
    )

    # Strict Constrained Generator loops back to NLI Groundedness Judge
    graph.add_edge("strict_retry_node", "groundedness_check_node")

    # Safe Refusal & Verbatim Fallback terminates to END / Output Guard
    graph.add_edge("safe_fallback_node", END)

    return graph.compile()


_crag_graph = _build_crag_graph()


# ── Public API ────────────────────────────────────────────────────────────────

async def run_crag_async(
    session_id: str,
    question: str,
    user_id: str | None = None,
    conversation_history: Any = "",
    *, external_evidence_policy: str = "document_only", approved_public_query: str = "",
) -> Dict[str, Any]:
    """Asynchronously execute the CRAG workflow without blocking the event loop."""
    try:
        doc_session_id = session_id
        has_docs = await asyncio.to_thread(vs.has_documents, doc_session_id)
        if not has_docs and user_id:
            user_has_docs = await asyncio.to_thread(vs.has_documents, user_id)
            if user_has_docs:
                doc_session_id = user_id
                has_docs = True

        doc_names = (
            await asyncio.to_thread(vs.list_document_names, doc_session_id)
            if has_docs
            else []
        )
        doc_profiles = (
            await asyncio.to_thread(vs.get_document_profiles, doc_session_id)
            if has_docs
            else []
        )
    except Exception as e:
        logger.warning("Could not fetch vector store details: %s. Assuming no docs.", e)
        has_docs = False
        doc_names = []
        doc_profiles = []
        doc_session_id = session_id

    initial_state: CRAGState = {
        "evidence_status": "",
        "retrieval_corrections_used": 0,
        "retained_evidence": [],
        "external_evidence_policy": external_evidence_policy,
        "approved_public_query": approved_public_query[:1000],
        "external_search_used": False,
        "missing_requirements": "",
        "question": question,
        "conversation_history": conversation_history,
        "session_id": doc_session_id,
        "has_documents": has_docs,
        "document_names": doc_names,
        "document_profiles": doc_profiles,
        "route": "",
        "chunks": [],
        "refined_chunks": [],
        "evaluation_result": "",
        "evaluation_reason": "",
        "db_retry_count": 0,
        "transformed_query": "",
        "web_results": [],
        "answer": "",
        "source": "",
        "citations": [],
        "is_grounded": True,
        "groundedness_reason": "",
        "groundedness_retry_count": 0,
        "contextualized_query": "",
        "nli_verdict": "",
        "nli_score": 1.0,
    }

    run_config = {
        "recursion_limit": 25,
        "tags": ["cortex", "crag-workflow"],
        "metadata": {"session_id": session_id, "question": question[:50]},
    }
    final_state = await _crag_graph.ainvoke(initial_state, config=run_config)

    valid_doc_sources = {c.get("source") for c in final_state.get("chunks", []) if c.get("source")}
    valid_web_urls = {r.get("url") for r in final_state.get("web_results", []) if r.get("url")}

    return {
        "answer": final_state.get("answer", ""),
        "source": final_state.get("source", "llm"),
        "citations": final_state.get("citations", []),
        "route": final_state.get("route", "llm"),
        "router_decision": final_state.get("router_decision", {}),
        "chunks": final_state.get("chunks", []) or final_state.get("refined_chunks", []),
        "web_results": final_state.get("web_results", []),
        "evidence_status": final_state.get("evidence_status") or None,
        "retrieval_status": final_state.get("retrieval_status"),
        "retrieval_corrections_used": final_state.get("retrieval_corrections_used", 0),
        "missing_requirements": final_state.get("missing_requirements", ""),
        "evidence_assessment": final_state.get("evidence_assessment", {}),
        "evaluation_result": final_state.get("evaluation_result", ""),
        "evaluation_reason": final_state.get("evaluation_reason", ""),
        "is_grounded": final_state.get("is_grounded", True),
        "groundedness_reason": final_state.get("groundedness_reason", ""),
        "transformed_query": final_state.get("transformed_query", ""),
        "contextualized_query": final_state.get("contextualized_query", ""),
        "nli_verdict": final_state.get("nli_verdict", ""),
        "nli_score": final_state.get("nli_score", 1.0),
        "valid_doc_sources": valid_doc_sources,
        "valid_web_urls": valid_web_urls,
    }


def run_crag(session_id: str, question: str, user_id: str | None = None) -> Dict[str, Any]:
    """Synchronous entrypoint."""
    return asyncio.run(run_crag_async(session_id, question, user_id=user_id))
