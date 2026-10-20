"""Generate one candidate; repairs share a single request-level allowance."""
from __future__ import annotations

import asyncio

from guardrails.output import scrub_output
from services.answer_contracts import EvidencePassage, GenerationResult
from services.generation import build_snapshot, generate_answer_async
from workflows.crag.state import CRAGState


def operational_response(state: CRAGState, message: str, status: str = "UNKNOWN") -> CRAGState:
    return {**state, "answer": scrub_output(message), "citations": [], "source": "guardrail",
            "verification_status": status, "is_grounded": False if status == "UNSUPPORTED" else None,
            "nli_verdict": "NOT_CHECKED", "nli_score": None}


async def direct_answer_node(state: CRAGState) -> CRAGState:
    request_started = False
    try:
        request_started = True
        result = await generate_answer_async(
            state["question"], [], source="llm", conversation_history=state.get("conversation_history", ""),
        )
    except (TimeoutError, asyncio.TimeoutError):
        result = GenerationResult(status="TIMEOUT", error_kind="timeout", source="llm", request_made=request_started)
    except Exception:
        result = GenerationResult(status="ERROR", error_kind="provider_error", source="llm")
    telemetry = [{"stage": "generation", **result.model_dump(exclude={"answer", "claims", "citations"})}]
    if result.status != "SUCCESS":
        return {**operational_response(state, "I could not generate an answer right now. Please try again."),
                "generation_status": result.status, "answer_attempts": telemetry}
    return {**state, "answer": result.answer, "citations": [], "source": "llm", "generation_status": "SUCCESS",
            "verification_status": "SKIPPED", "is_grounded": None, "nli_verdict": "NOT_CHECKED", "nli_score": None,
            "groundedness_reason": "No source verification applies to this direct answer.", "answer_attempts": telemetry}


async def generate_node(state: CRAGState) -> CRAGState:
    chunks, web = state.get("chunks", []), state.get("web_results", [])
    source = "hybrid" if chunks and web else "web_search" if web or state.get("route") == "web_search" else "rag"
    request_started = False
    try:
        if "generation_snapshot" in state:
            snapshot = [EvidencePassage.model_validate(p) for p in state["generation_snapshot"]]
        else:
            snapshot, truncated = build_snapshot(chunks, web)
            state["generation_snapshot"] = [p.model_dump() for p in snapshot]
            if truncated:
                state["evidence_status"] = "PARTIAL"
                state["missing_requirements"] = (state.get("missing_requirements", "") + " Some evidence was omitted by the generation context budget.")[:1000]
            state["snapshot_truncated"] = truncated
        prior = GenerationResult.model_validate(state["generation_result"]) if state.get("generation_result") else None
        request_started = True
        result = await generate_answer_async(
            state["question"], snapshot, source=source, evidence_status=state.get("evidence_status") or None,
            missing_requirements=state.get("missing_requirements", ""), conflicting_ids=state.get("conflicting_ids", []),
            conversation_history=state.get("conversation_history", ""),
            previous_draft=prior.answer if prior else "", feedback=state.get("repair_feedback"),
        )
    except (TimeoutError, asyncio.TimeoutError):
        result = GenerationResult(status="TIMEOUT", error_kind="timeout", source=source, request_made=request_started)
    except Exception:
        result = GenerationResult(status="ERROR", error_kind="invalid_snapshot", source=source)
    return {**state, "answer": "", "citations": [], "source": source, "is_grounded": None,
            "verification_status": "UNKNOWN", "generation_status": result.status,
            "generation_result": result.model_dump(),
            "answer_attempts": state.get("answer_attempts", []) + [{"stage": "generation", **result.model_dump(exclude={"answer", "claims", "citations"})}]}


async def strict_constrained_generator_node(state: CRAGState) -> CRAGState:
    if state.get("answer_repairs_used", 0) >= 1:
        return {**state, "generation_result": GenerationResult(status="ERROR", error_kind="repair_exhausted").model_dump()}
    return await generate_node({**state, "answer_repairs_used": 1, "groundedness_retry_count": 1})
