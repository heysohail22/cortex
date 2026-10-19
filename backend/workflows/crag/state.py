"""
CRAG State — State schema for Corrective Retrieval-Augmented Generation.
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal
from typing_extensions import TypedDict


class CRAGState(TypedDict):
    evidence_status: str
    retrieval_status: str
    retrieval_deadline: float
    retrieval_corrections_used: int
    retained_evidence: List[Dict[str, Any]]
    evidence_assessment: Dict[str, Any]
    conflicting_ids: List[str]
    missing_requirements: str
    clarification: str
    correction_action: str
    finalize_action: str
    external_evidence_policy: str
    approved_public_query: str
    external_search_used: bool
    external_evidence_status: str
    router_decision: Dict[str, Any]
    question: str
    conversation_history: Any           # Prior dialogue context for answer generation (native turns or str)
    session_id: str
    has_documents: bool
    document_names: List[str]
    document_profiles: List[Dict[str, Any]]
    route: str                          # "rag" | "llm" | "web_search"
    
    # Retrieval & Evaluation
    chunks: List[Dict[str, Any]]        # Raw chunks from Supabase vector store
    refined_chunks: List[Dict[str, Any]]# Relevant, de-noised chunks
    evaluation_result: str              # "CORRECT" | "INCORRECT" | "AMBIGUOUS"
    evaluation_reason: str
    db_retry_count: int                 # 0 = initial, 1 = re-retrieved from DB
    
    # Query Transformation & Web Augmentation
    transformed_query: str              # Active query being executed
    db_rewritten_query: str             # Bundled query for vector DB retry
    web_rewritten_query: str            # Bundled query for Tavily web search
    web_results: List[Dict[str, Any]]   # Results from Tavily web search
    
    # Output & Groundedness
    answer: str
    source: str                         # "rag" | "web_search" | "hybrid" | "llm"
    citations: List[str]
    is_grounded: bool                   # Independent Judge result
    groundedness_reason: str
    groundedness_retry_count: int       # Guard against infinite hallucination retry loops
    contextualized_query: str           # Resolved standalone query from Query Contextualizer
    nli_verdict: str                    # "ENTAILMENT" | "NEUTRAL" | "CONTRADICTION"
    nli_score: float                    # Entailment probability / score (0.0 to 1.0)
