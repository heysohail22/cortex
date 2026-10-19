"""Verify the displayed candidate against exactly the generation evidence snapshot."""
from __future__ import annotations

import asyncio
from guardrails.output import scrub_output

from services.answer_contracts import EvidencePassage, GenerationResult, VerificationResult
from services.verification import verify_answer_async
from workflows.crag.nodes.generation import operational_response, remaining_time
from workflows.crag.state import CRAGState
import config


async def groundedness_check_node(state: CRAGState) -> CRAGState:
    request_started = False
    try:
        generation = GenerationResult.model_validate(state["generation_result"])
        if generation.error_kind == "no_evidence":
            return {**operational_response(state, "I could not find supporting evidence to answer this question. Please provide a relevant source or clarify your question.", "SKIPPED"),
                    "route": "no_answer_evidence"}
        snapshot = [EvidencePassage.model_validate(p) for p in state.get("generation_snapshot", [])]
        limit = remaining_time(state, config.TIMEOUT_GROUNDEDNESS)
        if limit <= 0:
            raise TimeoutError()
        request_started = True
        result = await asyncio.wait_for(verify_answer_async(
            state["question"], generation, snapshot, evidence_status=state.get("evidence_status"),
            missing_requirements=state.get("missing_requirements", ""),
            timeout=limit,
        ), timeout=limit)
    except Exception:
        result = VerificationResult(status="UNKNOWN", reason="Verification unavailable.", request_made=request_started)
    attempts = state.get("answer_attempts", []) + [{"stage": "verification", **result.model_dump()}]
    update = {**state, "verification_status": result.status, "groundedness_reason": scrub_output(result.reason),
              "is_grounded": True if result.status == "SUPPORTED" else False if result.status == "UNSUPPORTED" else None,
              "nli_verdict": "ENTAILMENT" if result.status == "SUPPORTED" else "NEUTRAL" if result.status == "UNSUPPORTED" else "NOT_CHECKED",
              "nli_score": None, "answer_attempts": attempts,
              "repair_feedback": result.model_dump(exclude={"usage", "elapsed_ms", "model", "provider"})}
    if result.status == "SUPPORTED":
        return {**update, "answer": generation.answer, "citations": generation.citations}
    return {**update, "answer": "", "citations": []}


async def safe_fallback_node(state: CRAGState) -> CRAGState:
    unsupported = state.get("verification_status") == "UNSUPPORTED"
    message = ("I could not verify a supported answer from the available evidence. Please provide more information or clarify your question."
               if unsupported else "I could not complete answer verification right now. Please try again shortly.")
    return {**operational_response(state, message, "UNSUPPORTED" if unsupported else "UNKNOWN"),
            "route": "hallucination_fallback" if unsupported else "answer_unavailable"}
