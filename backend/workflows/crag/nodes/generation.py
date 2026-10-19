from __future__ import annotations

import asyncio
import logging
from typing import cast

import config
from workflows.crag.state import CRAGState

logger = logging.getLogger(__name__)

from services.generation import generate_direct_answer_async, generate_rag_answer_async, generate_web_answer_async, generate_hybrid_answer_async


async def direct_answer_node(state: CRAGState) -> CRAGState:
    try:
        result = await asyncio.wait_for(
            generate_direct_answer_async(
                question=state["question"], conversation_history=state.get("conversation_history", ""),
            ), timeout=config.TIMEOUT_GENERATION,
        )
        answer = result.get("answer", "")
    except Exception:
        logger.warning("Direct generation unavailable")
        answer = "I could not generate an answer right now. Please try again."
    return {**state, "answer": answer, "source": "llm", "is_grounded": False}


async def generate_node(state: CRAGState) -> CRAGState:
    question = state["question"]
    eval_result = state.get("evaluation_result", "CORRECT")
    chunks = state.get("chunks", [])
    web_results = state.get("web_results", [])
    retry_count = state.get("groundedness_retry_count", 0)
    strict_mode = retry_count > 0

    conversation_history = state.get("conversation_history", "")
    try:
        evidence_status = state.get("evidence_status")
        evidence_options = {
            "evidence_status": evidence_status,
            "missing_requirements": state.get("missing_requirements", ""),
        } if evidence_status else {}
        if evidence_status and not web_results:
            coro = generate_rag_answer_async(
                question, chunks, strict=strict_mode, conversation_history=conversation_history,
                **evidence_options,
            )
        elif evidence_status and chunks and web_results:
            coro = generate_hybrid_answer_async(
                question, chunks, web_results, conversation_history=conversation_history,
                **evidence_options,
            )
        elif evidence_status and web_results:
            coro = generate_web_answer_async(
                question, web_results, conversation_history=conversation_history,
            )
        elif eval_result == "CORRECT":
            coro = generate_rag_answer_async(
                question, chunks, strict=strict_mode, conversation_history=conversation_history
            )
        elif eval_result == "INCORRECT":
            coro = generate_web_answer_async(
                question, web_results, conversation_history=conversation_history
            )
        else:  # AMBIGUOUS
            coro = generate_hybrid_answer_async(
                question, chunks, web_results, conversation_history=conversation_history
            )

        result = await asyncio.wait_for(coro, timeout=config.TIMEOUT_GENERATION)
    except asyncio.TimeoutError:
        logger.warning("Generation node timed out after %.1fs.", config.TIMEOUT_GENERATION)
        result = {
            "answer": "I apologize, but answering your request took longer than expected. Please try again or simplify your question.",
            "source": "llm",
            "citations": [],
        }
    except Exception as e:
        logger.exception("Generation error: %s", e)
        result = {
            "answer": "An error occurred while generating the answer. Please try again.",
            "source": "llm",
            "citations": [],
        }

    return {
        **state,
        "answer": result["answer"],
        "source": result["source"],
        "citations": result["citations"],
    }


async def strict_constrained_generator_node(state: CRAGState) -> CRAGState:
    """Strict Constrained Generator (Temperature 0.0 Retry) upon NLI contradiction/neutral."""
    question = state["question"]
    chunks = state.get("chunks", [])
    retry_count = state.get("groundedness_retry_count", 0)
    conversation_history = state.get("conversation_history", "")

    logger.warning(
        "Strict Constrained Generator: Re-generating answer with temperature 0.0 strict factuality (retry %d).",
        retry_count + 1,
    )

    try:
        result = await asyncio.wait_for(
            generate_rag_answer_async(
                question,
                chunks,
                strict=True,
                conversation_history=conversation_history,
                evidence_status=state.get("evidence_status"),
                missing_requirements=state.get("missing_requirements", ""),
            ),
            timeout=config.TIMEOUT_GENERATION,
        )
    except asyncio.TimeoutError:
        logger.warning("Strict generation node timed out after %.1fs.", config.TIMEOUT_GENERATION)
        result = {
            "answer": "I apologize, but verifying the answer took longer than expected.",
            "source": "llm",
            "citations": [],
        }
    except Exception as e:
        logger.exception("Strict constrained generation error: %s", e)
        result = {
            "answer": "An error occurred during strict constrained generation.",
            "source": "llm",
            "citations": [],
        }

    return {
        **state,
        "answer": result["answer"],
        "source": result["source"],
        "citations": result["citations"],
        "groundedness_retry_count": retry_count + 1,
    }
