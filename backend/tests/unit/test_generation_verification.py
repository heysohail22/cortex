from __future__ import annotations

import asyncio
import time
from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, patch

import pytest

from providers.structured import StructuredResponse, InvalidProviderOutput
from services.answer_contracts import GenerationResult, VerificationResult
from services.evidence import RetrievalEvaluation
from services.generation import build_snapshot, generate_answer_async, validate_support
from services.verification import verify_answer_async
from workflows.crag.graph import _build_crag_graph
from workflows.crag.nodes import generation as gn, verification as vn

DOC = {"source": "policy.pdf", "text": "Employees receive 20 annual leave days. The fee is not specified."}
WEB = {"url": "https://public.example/rule", "title": "Public rule", "content": "A public consumer rule permits 14 days."}


def draft(snapshot, answer="Employees receive 20 annual leave days."):
    return {"answer": answer, "claims": [{"text": "Employees receive 20 annual leave days.", "evidence_ids": [snapshot[0].id], "source_kind": "document"}]}


def judgement(status="SUPPORTED", **kwargs):
    return {"status": status, "checked_claim_indices": [0], "unsupported_claim_indices": [0] if status == "UNSUPPORTED" else [],
            "invalid_evidence_ids": [], "uncovered_claims": [], "reason": status, "confidence": None, **kwargs}


def response(data):
    return StructuredResponse(data=data, model="test-model", usage={"prompt_tokens": 100, "completion_tokens": 20})


async def generated(snapshot=None, **kwargs):
    snapshot = snapshot if snapshot is not None else build_snapshot([DOC], [])[0]
    payload = kwargs.pop("payload", draft(snapshot))
    with patch("services.generation.generate_structured", AsyncMock(return_value=response(payload))):
        result = await generate_answer_async("What is the leave allowance?", snapshot, source="rag", **kwargs)
    return result, snapshot


async def test_generation_scrubs_before_verification_and_maps_only_cited_sources():
    snapshot, _ = build_snapshot([DOC, {"source": "unused.pdf", "text": "Irrelevant."}], [])
    result, _ = await generated(snapshot, payload=draft(snapshot, "Employees receive 20 annual leave days.\nSource: unused.pdf"))
    assert result.status == "SUCCESS"
    assert "Source:" not in result.answer
    assert result.citations == ["policy.pdf"]
    assert result.usage["completion_tokens"] == 20
    with patch("services.verification.generate_structured", AsyncMock(return_value=response(judgement()))) as judge:
        verdict = await verify_answer_async("q", result, snapshot)
    assert verdict.status == "SUPPORTED"
    assert judge.call_args.kwargs["payload"]["answer"] == result.answer
    assert judge.call_args.kwargs["payload"]["evidence"] == [p.model_dump() for p in snapshot]


@pytest.mark.parametrize("invalid", ["id", "kind", "span", "empty_claims", "empty_answer"])
async def test_invalid_generation_is_typed_and_never_supported(invalid):
    snapshot, _ = build_snapshot([DOC], [])
    payload = draft(snapshot)
    if invalid == "id": payload["claims"][0]["evidence_ids"] = ["forged"]
    if invalid == "kind": payload["claims"][0]["source_kind"] = "web"
    if invalid == "span": payload["claims"][0]["text"] = "not in answer"
    if invalid == "empty_claims": payload["claims"] = []
    if invalid == "empty_answer": payload["answer"] = ""
    result, _ = await generated(snapshot, payload=payload)
    assert result.status == "ERROR" and result.error_kind == "invalid_output"
    with patch("services.verification.generate_structured", AsyncMock()) as judge:
        verdict = await verify_answer_async("q", result, snapshot)
    assert verdict.status == "UNSUPPORTED"
    judge.assert_not_awaited()


@pytest.mark.parametrize("failure,expected", [(RuntimeError(), "ERROR"), (TimeoutError(), "TIMEOUT"), (InvalidProviderOutput(), "ERROR")])
async def test_provider_failures_are_not_answers(failure, expected):
    snapshot, _ = build_snapshot([DOC], [])
    with patch("services.generation.generate_structured", AsyncMock(side_effect=failure)):
        result = await generate_answer_async("q", snapshot, source="rag")
    assert result.status == expected and not result.answer


async def test_no_evidence_does_not_call_generator():
    with patch("services.generation.generate_structured", AsyncMock()) as invoke:
        result = await generate_answer_async("q", [], source="rag", evidence_status="NONE")
    assert result.error_kind == "no_evidence"
    invoke.assert_not_awaited()


async def test_direct_answer_has_no_citations_and_skips_judge():
    with patch("services.generation.generate_structured", AsyncMock(return_value=response({"answer": "Hello!", "claims": []}))):
        result = await generate_answer_async("Hello", [], source="llm")
    with patch("services.verification.generate_structured", AsyncMock()) as judge:
        verification = await verify_answer_async("Hello", result, [])
    assert result.status == "SUCCESS" and not result.citations
    assert verification.status == "SKIPPED"
    judge.assert_not_awaited()


@pytest.mark.parametrize("payload,expected", [
    (judgement(checked_claim_indices=[]), "UNKNOWN"),
    (judgement(unsupported_claim_indices=[0]), "UNSUPPORTED"),
    (judgement(uncovered_claims=["Invented carryover rule"]), "UNSUPPORTED"),
    (judgement(checked_claim_indices=[99]), "UNKNOWN"),
    (judgement(confidence=float("nan")), "UNKNOWN"),
    (judgement(confidence=1.5), "UNKNOWN"),
    (judgement(invalid_evidence_ids=["forged"]), "UNKNOWN"),
    ({"status": "SUPPORTED"}, "UNKNOWN"),
])
async def test_judge_requires_complete_valid_coverage(payload, expected):
    result, snapshot = await generated()
    with patch("services.verification.generate_structured", AsyncMock(return_value=response(payload))):
        verdict = await verify_answer_async("q", result, snapshot)
    assert verdict.status == expected


async def test_judge_failure_is_unknown_without_confidence():
    result, snapshot = await generated()
    with patch("services.verification.generate_structured", AsyncMock(side_effect=TimeoutError())):
        verdict = await verify_answer_async("q", result, snapshot)
    assert verdict.status == "UNKNOWN" and verdict.confidence is None


async def test_partial_and_mixed_evidence_are_sent_with_precise_attribution():
    snapshot, _ = build_snapshot([DOC], [WEB])
    payload = draft(snapshot, "Employees receive 20 annual leave days. The fee is missing. A public rule permits 14 days.")
    payload["claims"].append({"text": "A public rule permits 14 days.", "evidence_ids": [snapshot[1].id], "source_kind": "web"})
    with patch("services.generation.generate_structured", AsyncMock(return_value=response(payload))) as provider:
        result = await generate_answer_async("q", snapshot, source="hybrid", evidence_status="PARTIAL", missing_requirements="fee")
    assert result.status == "SUCCESS" and result.citations == [DOC["source"], WEB["url"]]
    with patch("services.verification.generate_structured", AsyncMock(return_value=response(judgement(checked_claim_indices=[0, 1])))) as judge:
        verdict = await verify_answer_async("q", result, snapshot, evidence_status="PARTIAL", missing_requirements="fee")
    assert verdict.status == "SUPPORTED"
    assert provider.call_args.kwargs["payload"]["missing_requirements"] == "fee"
    assert judge.call_args.kwargs["payload"]["evidence_status"] == "PARTIAL"


def test_snapshot_budget_is_exact_and_never_restores_omitted_tails():
    with patch("config.MAX_GENERATION_CONTEXT_CHARS", 350):
        snapshot, truncated = build_snapshot([{**DOC, "text": "\\\"" * 2000}], [WEB])
    assert truncated
    assert sum(len(p.model_dump_json()) + 2 for p in snapshot) <= 350
    assert snapshot and len(snapshot[0].text) < 4000


async def run_graph_with_results(generation_responses, judge_responses, **initial):
    selected = RetrievalEvaluation(status="SUFFICIENT", chunks=[DOC])
    with patch("workflows.crag.nodes.router.classify_async", AsyncMock(return_value={"route": "rag"})), \
         patch("workflows.crag.nodes.retrieval.vs.similarity_search", return_value=[DOC]) as retrieve, \
         patch("workflows.crag.nodes.retrieval.evaluate_retrieval_async", AsyncMock(return_value=selected)), \
         patch("services.generation.generate_structured", AsyncMock(side_effect=generation_responses)) as gen, \
         patch("services.verification.generate_structured", AsyncMock(side_effect=judge_responses)) as judge:
        final = await _build_crag_graph().ainvoke({"question": "How many annual leave days?", "has_documents": True, "session_id": "s", **initial})
    return final, gen, judge, retrieve


async def test_success_graph_one_generation_one_check():
    snapshot, _ = build_snapshot([DOC], [])
    final, gen, judge, retrieve = await run_graph_with_results([response(draft(snapshot))], [response(judgement())])
    assert final["verification_status"] == "SUPPORTED" and final["is_grounded"] is True
    assert gen.await_count == judge.await_count == retrieve.call_count == 1
    assert final.get("answer_repairs_used", 0) == 0
    assert len(final["answer_attempts"]) == 2


async def test_repair_once_uses_identical_snapshot_and_no_retrieval_restart():
    snapshot, _ = build_snapshot([DOC], [])
    final, gen, judge, retrieve = await run_graph_with_results(
        [response(draft(snapshot)), response(draft(snapshot))],
        [response(judgement("UNSUPPORTED")), response(judgement())])
    assert final["verification_status"] == "SUPPORTED" and final["answer_repairs_used"] == 1
    assert gen.await_count == judge.await_count == 2 and retrieve.call_count == 1
    assert gen.call_args_list[0].kwargs["payload"]["evidence"] == gen.call_args_list[1].kwargs["payload"]["evidence"]
    assert gen.call_args_list[1].kwargs["payload"]["draft"]
    assert gen.call_args_list[1].kwargs["payload"]["repair_feedback"]["status"] == "UNSUPPORTED"


async def test_rejected_repair_returns_limitation_without_draft_or_citations():
    snapshot, _ = build_snapshot([DOC], [])
    final, gen, judge, retrieve = await run_graph_with_results(
        [response(draft(snapshot)), response(draft(snapshot))], [response(judgement("UNSUPPORTED"))] * 2)
    assert gen.await_count == judge.await_count == 2
    assert final["verification_status"] == "UNSUPPORTED" and final["is_grounded"] is False
    assert not final["citations"] and "20 annual" not in final["answer"]


async def test_invalid_generation_consumes_same_repair_allowance():
    snapshot, _ = build_snapshot([DOC], [])
    invalid = draft(snapshot); invalid["claims"][0]["evidence_ids"] = ["invented"]
    final, gen, judge, retrieve = await run_graph_with_results([response(invalid), response(draft(snapshot))], [response(judgement())])
    assert gen.await_count == 2 and judge.await_count == 1
    assert final["answer_repairs_used"] == 1 and final["verification_status"] == "SUPPORTED"


async def test_unknown_judge_stops_without_repair_or_draft():
    snapshot, _ = build_snapshot([DOC], [])
    final, gen, judge, _ = await run_graph_with_results([response(draft(snapshot))], [TimeoutError()])
    assert gen.await_count == judge.await_count == 1
    assert final["verification_status"] == "UNKNOWN" and final["is_grounded"] is None
    assert final["nli_score"] is None and not final["citations"]
    assert "20 annual" not in final["answer"]




async def test_generation_context_truncation_discloses_partial():
    async def generate(*args, **kwargs):
        assert kwargs["evidence_status"] == "PARTIAL"
        assert "omitted" in kwargs["missing_requirements"]
        return GenerationResult(status="ERROR", error_kind="provider_error")
    with patch("config.MAX_GENERATION_CONTEXT_CHARS", 220), patch.object(gn, "generate_answer_async", side_effect=generate):
        result = await gn.generate_node({"question": "q", "chunks": [{**DOC, "text": "fact " * 1000}], "evidence_status": "SUFFICIENT"})
    assert result["snapshot_truncated"] and result["evidence_status"] == "PARTIAL"


async def test_web_answer_is_verified_not_skipped():
    snapshot, _ = build_snapshot([], [WEB])
    payload = {"answer": "A public consumer rule permits 14 days.", "claims": [{"text": "A public consumer rule permits 14 days.", "evidence_ids": [snapshot[0].id], "source_kind": "web"}]}
    with patch("services.generation.generate_structured", AsyncMock(return_value=response(payload))):
        result = await gn.generate_node({"question": "public rules?", "route": "web_search", "web_results": [WEB]})
    with patch("services.verification.generate_structured", AsyncMock(return_value=response(judgement()))) as judge:
        result = await vn.groundedness_check_node(result)
    judge.assert_awaited_once()
    assert result["verification_status"] == "SUPPORTED"




def test_comparison_cost_includes_thinking_and_does_not_assume_missing_usage_is_free():
    from evals.compare_generation import estimate_cost
    rates = {"gemini:pinned": {"input_per_million": 1, "output_per_million": 2}}
    attempts = [{"provider": "gemini", "model": "pinned", "usage": {"prompt_token_count": 100, "candidates_token_count": 20, "thoughts_token_count": 30}}]
    assert estimate_cost(attempts, rates) == pytest.approx(0.0002)
    assert estimate_cost([{**attempts[0], "usage": None}], rates) is None
    assert estimate_cost(attempts, {}) is None


def test_comparison_dataset_has_32_reviewable_cases():
    from pathlib import Path
    import json
    cases = json.loads((Path(__file__).parents[2]/"evals/datasets/generation_comparison.json").read_text())
    assert len(cases) == 32 and len({c["id"] for c in cases}) == 32
    assert {"rag", "web_search", "hybrid", "llm"} <= {c["source"] for c in cases}
    assert all(c["reference_answer"] and c["review_status"] for c in cases)


async def test_empty_web_results_return_unverified_limitation_without_model_calls():
    with patch("services.generation.generate_structured", AsyncMock()) as generate, patch("services.verification.generate_structured", AsyncMock()) as judge:
        state = await gn.generate_node({"question": "q", "route": "web_search", "web_results": []})
        state = await vn.groundedness_check_node(state)
    generate.assert_not_awaited()
    judge.assert_not_awaited()
    assert state["verification_status"] == "SKIPPED" and state["is_grounded"] is None
    assert state["answer"] and not state["citations"]


async def test_generation_rate_limit_is_reported_as_provider_capacity_not_verification_failure():
    error = RuntimeError('rate limited')
    error.status_code = 429
    snapshot, _ = build_snapshot([DOC], [])
    with patch('services.generation.generate_structured', AsyncMock(side_effect=error)):
        result = await generate_answer_async('q', snapshot, source='rag')
    assert result.status == 'ERROR' and result.error_kind == 'rate_limited'
    state = await vn.safe_fallback_node({'generation_result': result.model_dump(), 'verification_status': 'UNKNOWN'})
    assert 'rate-limited' in state['answer']
    assert state['route'] == 'answer_unavailable'
    assert state['is_grounded'] is None
