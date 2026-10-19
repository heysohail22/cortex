from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException
from api.schemas.chat import ChatRequest, DeleteSessionResponse, ChunkInfo, WebResultInfo, ChatResponse

import config
from workflows.crag import run_crag_async
from guardrails import (
    check_prompt_async,
    process_output,
    rate_limit,
    redact_pii_async,
)
from repositories import storage as storage_service, documents as vs
from services.conversations import get_native_conversation_turns
from repositories.conversations import (
    delete_conversation,
    get_all_sessions_summary,
    save_turn,
)

logger = logging.getLogger(__name__)
_chat_slots = asyncio.Semaphore(config.MAX_CONCURRENT_CHATS)

router = APIRouter(prefix="/api", tags=["chat"])


@router.post(
    "/chat",
    response_model=ChatResponse,
    dependencies=[
        Depends(
            rate_limit(
                config.RATE_LIMIT_CHAT_REQUESTS,
                config.RATE_LIMIT_CHAT_WINDOW,
            )
        )
    ],
)
async def chat(request: ChatRequest):
    try:
        await asyncio.wait_for(_chat_slots.acquire(), timeout=0.05)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=503, detail="Server is busy. Please retry shortly.", headers={"Retry-After": "1"})
    try:
        return await _chat_impl(request)
    finally:
        _chat_slots.release()


async def _chat_impl(request: ChatRequest):
    try:
        # ── Layer 1 Guardrail: Prompt Injection & Jailbreak Defense ───────────
        guard_res = await check_prompt_async(request.message)
        if not guard_res.is_safe:
            logger.warning(
                "Blocked unsafe prompt for session %s: %s (%s)",
                request.session_id,
                guard_res.violation_type,
                guard_res.reason,
            )
            return ChatResponse(
                answer=(
                    "I cannot fulfill this request as it appears to contain unauthorized instructions "
                    "or system overrides. Please refine your query."
                ),
                source="guardrail",
                citations=[],
                route="guardrail_blocked",
                suggest_web_search=False,
            )

        # ── Layer 1 Guardrail: PII & Sensitive Data Redaction ─────────────────
        pii_res = await redact_pii_async(request.message)
        processed_query = pii_res.sanitized_text

        # ── Conversation Memory (Native Turns) ─────────────────────────────
        # Fetch prior dialogue turns as native LangChain messages (summarized
        # if over budget) while keeping the retrieval query 100% clean.
        prior_turns = await get_native_conversation_turns(request.session_id)

        # ── CRAG Workflow Execution ───────────────────────────────────────────
        result = await run_crag_async(
            session_id=request.session_id,
            question=processed_query,
            user_id=request.user_id,
            conversation_history=prior_turns,
        )

        # ── Layer 3 Guardrail: Output Scrubbing & Citation Verification ───────
        clean_answer, clean_citations = process_output(
            answer=result.get("answer", ""),
            citations=result.get("citations", []),
            valid_doc_sources=result.get("valid_doc_sources", set()),
            valid_web_urls=result.get("valid_web_urls", set()),
        )

        # Never keep approval for text or references changed after verification.
        if result.get("verification_status") == "SUPPORTED" and (
            clean_answer != result.get("answer", "") or clean_citations != result.get("citations", [])
        ):
            clean_answer, clean_citations = process_output(
                "I could not complete answer verification right now. Please try again shortly.", [],
            )
            result.update(verification_status="UNKNOWN", is_grounded=None, nli_score=None,
                          nli_verdict="NOT_CHECKED", source="guardrail", route="answer_unavailable",
                          groundedness_reason="Output changed after verification.")

        # Persist this turn to chat_history so future questions have context.
        # We save the redacted query (not raw) to avoid storing PII in Supabase.
        save_turn(request.session_id, user_message=processed_query, assistant_message=clean_answer)

        raw_chunks = result.get("chunks", [])
        clean_chunks = [
            ChunkInfo(
                source=c.get("source", "Unknown"),
                text=c.get("text", ""),
                similarity=c.get("similarity"),
            )
            for c in raw_chunks
            if c.get("text")
        ]

        raw_web = result.get("web_results", [])
        clean_web = [
            WebResultInfo(
                title=w.get("title", "Web Source"),
                url=w.get("url", ""),
                content=w.get("content", ""),
            )
            for w in raw_web
            if w.get("url") or w.get("content")
        ]

        return ChatResponse(
            answer=clean_answer,
            source=result.get("source", "llm"),
            citations=clean_citations,
            route=result.get("route", "llm"),
            suggest_web_search=result.get("source") == "web_search",
            chunks=clean_chunks,
            web_results=clean_web,
            evidence_status=result.get("evidence_status"),
            retrieval_status=result.get("retrieval_status"),
            retrieval_corrections_used=result.get("retrieval_corrections_used", 0),
            evaluation_result=result.get("evaluation_result") or None,
            evaluation_reason=result.get("evaluation_reason") or None,
            verification_status=result.get("verification_status", "SKIPPED"),
            generation_status=result.get("generation_status"),
            answer_repairs_used=result.get("answer_repairs_used", 0),
            is_grounded=result.get("is_grounded"),
            groundedness_reason=result.get("groundedness_reason") or None,
            transformed_query=result.get("transformed_query") or None,
            nli_verdict=result.get("nli_verdict") or None,
            nli_score=result.get("nli_score"),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Chat error for session %s", request.session_id)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
async def list_sessions():
    """List all saved chat sessions and their messages from Supabase."""
    try:
        sessions = await asyncio.to_thread(get_all_sessions_summary)
        return {"sessions": sessions}
    except Exception as e:
        logger.warning("Could not fetch sessions from Supabase: %s", e)
        return {"sessions": []}


@router.delete("/sessions/{session_id}", response_model=DeleteSessionResponse)
async def delete_session(session_id: str):
    """Delete all conversation history, document chunks, and storage files associated with a session."""
    # Attempt cleanup on each component independently so offline/sleeping DB doesn't crash the deletion
    try:
        await asyncio.to_thread(delete_conversation, session_id)
    except Exception as e:
        logger.warning("Could not delete conversation for session %s (database may be sleeping): %s", session_id, e)

    try:
        await asyncio.to_thread(vs.delete_session_documents, session_id)
    except Exception as e:
        logger.warning("Could not delete document chunks for session %s: %s", session_id, e)

    try:
        await asyncio.to_thread(storage_service.delete_session_files, session_id)
    except Exception as e:
        logger.warning("Could not delete storage files for session %s: %s", session_id, e)

    return DeleteSessionResponse(
        status="success",
        message=f"Session '{session_id}' deleted successfully",
    )
