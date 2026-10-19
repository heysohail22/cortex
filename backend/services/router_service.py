"""
Router Service — Intelligent, document-aware LLM classifier.
Uses Jev structured assessments with an explicit legacy Groq rollback.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field

import config

logger = logging.getLogger(__name__)


class RouteDecision(BaseModel):
    route: Literal["rag", "web_search", "direct_answer", "unsafe"] = Field(
        description=(
            "The selected execution route: "
            "'rag' for questions seeking facts, rules, procedures, or domain specifics contained within uploaded documents; "
            "'web_search' for live/current events, weather, stock prices, or recent news; "
            "'direct_answer' for greetings, identity/persona questions, general concepts, explanations, coding, or math; "
            "'unsafe' for requests asking for malware, cyberattacks, exploit payloads, dangerous weapons, harassment, or self-harm."
        )
    )
    reason: str = Field(
        default="",
        description="Brief 1-sentence reasoning for the chosen route based on query intent and document content context."
    )


# Only initialize the legacy provider when explicit rollback is selected.
_groq_router = None


def _get_groq_router():
    global _groq_router
    if _groq_router is None:
        _groq_router = ChatGroq(
            model=config.GROQ_REASONING_MODEL,
            api_key=config.GROQ_API_KEY,
            temperature=0.0,
        ).with_structured_output(RouteDecision)
    return _groq_router


def _format_documents(documents: list) -> str:
    """Format documents with filenames and extracted topics for the system prompt."""
    if not documents:
        return "None"
    lines = []
    for doc in documents:
        if isinstance(doc, dict):
            name = doc.get("filename") or doc.get("name") or "Unknown"
            topics = (doc.get("topics") or "").strip()
            if topics:
                lines.append(f'   - "{name}" (Topics: {topics})')
            else:
                lines.append(f'   - "{name}"')
        else:
            lines.append(f'   - "{doc}"')
    return "\n".join(lines)


def _build_system_prompt(has_documents: bool, documents: list) -> str:
    current_date = datetime.now(timezone.utc).strftime("%B %d, %Y")

    if has_documents and documents:
        doc_context = _format_documents(documents)
        rag_section = f"""- "rag": Inquiries seeking internal facts, proprietary guidelines, procedures, domain specifics, or data contained within the user's uploaded documents:
{doc_context}
  Choose "rag" when the question asks about, relates to, or can be answered by the content, policies, or topics of these uploaded documents (even if the user does not explicitly name the file)."""
    else:
        # Dynamic Token Pruning: omit RAG rule if no documents exist
        rag_section = """- "rag": (DISABLED: No documents are currently uploaded by the user)."""

    return f"""You are the intent classification engine for Cortex, an intelligent AI assistant.
Today's date is: {current_date}.

Analyze the user's active query and classify their primary intent into the single most appropriate execution route:

- "unsafe": Requests involving weapon creation, cyberattacks, exploit payloads, malware generation, severe harassment, or self-harm.

{rag_section}

- "web_search": Inquiries requiring real-time, live, or time-sensitive external information (such as today's breaking news, recent events, live financial markets, current weather, or begins with "Search the web for").

- "direct_answer": General knowledge, conceptual explanations, coding assistance, mathematical calculations, logic problems, creative writing, or casual greetings that do not require external documents or real-time data.

Decision Guidelines:
- If uploaded documents exist and the user query pertains to the subjects, policies, rules, specifications, or domain covered in those documents, ALWAYS route to "rag" so the system retrieves the relevant document chunks from the vector store.
- If a query is a general concept (e.g. "Explain binary search", "What is machine learning?", "Write a python script to reverse a string") that has no connection to the uploaded documents, choose "direct_answer".
- If the query requires current real-world events or live data outside of the uploaded documents, choose "web_search".
- Prioritize user safety ("unsafe") above all other routes."""



def _build_messages(question: str, has_documents: bool, documents: list) -> list:
    prompt = _build_system_prompt(has_documents, documents)
    return [
        SystemMessage(content=prompt),
        HumanMessage(content=f"User Query: {question}"),
    ]


async def _classify_groq_async(
    question: str,
    has_documents: bool,
    document_names: list | None = None,
    documents: list | None = None,
) -> Dict[str, Any]:
    """Classify with the legacy Groq provider when explicitly configured."""

    docs = documents if documents is not None else (document_names or [])
    messages = _build_messages(question, has_documents, docs)
    route, reason = "", ""

    # 1. Attempt Primary
    try:
        decision: RouteDecision = await asyncio.wait_for(
            _get_groq_router().ainvoke(messages),
            timeout=config.TIMEOUT_ROUTER,
        )
        route = decision.route
        reason = getattr(decision, "reason", "")
    except Exception as e:
        logger.warning("Legacy router unavailable (%s)", type(e).__name__)

    if not route:
        return {"route": "unavailable", "direct_answer": "Routing is temporarily unavailable. Please try again.", "reason": "router_error", "status": "error"}

    if route == "rag" and not has_documents:
        route = "direct_answer"
        reason = "No documents uploaded, defaulting to direct answer"

    direct_answer = ""
    if route == "unsafe":
        direct_answer = "I cannot provide assistance with malware, cyberattacks, exploit payloads, dangerous weapons, harassment, or self-harm."

    return {"route": route, "direct_answer": direct_answer, "reason": reason}


async def classify_async(
    question: str,
    has_documents: bool,
    document_names: list | None = None,
    documents: list | None = None,
    conversation_history: Any = "",
) -> Dict[str, Any]:
    if config.ROUTER_PROVIDER == "groq":
        return await _classify_groq_async(question, has_documents, document_names, documents)
    if config.ROUTER_PROVIDER != "jev":
        return {"route": "unavailable", "direct_answer": "Routing is temporarily unavailable. Please try again.", "status": "error", "reason": "invalid_provider"}
    from services.jev_service import classify_with_jev
    return await classify_with_jev(
        question, has_documents, documents if documents is not None else (document_names or []),
        conversation_history,
    )


def classify(
    question: str,
    has_documents: bool,
    document_names: list | None = None,
    documents: list | None = None,
) -> Dict[str, Any]:
    """Synchronous wrapper for classify_async."""
    return asyncio.run(classify_async(question, has_documents, document_names, documents))

