"""
Evaluation Runner — CLI and programmatic orchestrator for Cortex benchmarks.
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys
import time
from typing import Any, Dict, List, Optional

from workflows.crag import run_crag_async
from guardrails import check_prompt_async, process_output, redact_pii_async
from evals.datasets.samples import DEFAULT_BENCHMARK_DATASET, EvalSample, load_dataset
from retrieval import vector_store as vs
from repositories import documents
from evals.metrics.scoring import evaluate_sample_async
from evals.report import generate_markdown_report, print_cli_summary

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def _seed_eval_documents(session_id: str, sample_id: str, chunks: List[str]) -> str:
    """Upload mock chunks for an eval sample so the CRAG router sees documents."""
    source = f"eval_context_{sample_id}.txt"
    docs = [{"text": c, "source": source} for c in chunks]
    vs.add_documents(session_id, docs)
    return source


def _cleanup_eval_documents(session_id: str, source: str) -> None:
    """Remove seeded eval documents for the session."""
    try:
        documents.delete_document(session_id, source)
    except Exception as e:
        logger.warning("Failed to cleanup eval documents for %s: %s", session_id, e)


async def run_single_pipeline_test(sample: EvalSample) -> Dict[str, Any]:
    """Runs a single test sample through the end-to-end Cortex pipeline."""
    session_id = f"eval-{sample.id}"
    seeded_source = ""
    start_time = time.perf_counter()

    # Seed mock documents so the router/critic see uploaded files
    if sample.mock_chunks:
        try:
            seeded_source = await asyncio.to_thread(
                _seed_eval_documents, session_id, sample.id, sample.mock_chunks
            )
            logger.info("[%s] Seeded %d mock chunk(s) for eval session.", sample.id, len(sample.mock_chunks))
        except Exception as e:
            logger.warning("[%s] Failed to seed eval documents: %s", sample.id, e)

    try:
        # 1. Layer 1 Guardrail: Prompt Injection
        guard_res = await check_prompt_async(sample.question)
        if not guard_res.is_safe:
            latency = time.perf_counter() - start_time
            return {
                "answer": "Blocked by prompt injection guardrails.",
                "source": "guardrail",
                "citations": [],
                "route": "guardrail_blocked",
                "chunks": [],
                "latency_s": latency,
                "blocked": True,
            }

        # 2. Layer 1 Guardrail: PII Redaction
        pii_res = await redact_pii_async(sample.question)
        processed_query = pii_res.sanitized_text

        # 3. CRAG Workflow Execution
        crag_res = await run_crag_async(session_id=session_id, question=processed_query)

        # 4. Layer 3 Guardrail: Output Scrubbing & Citation Verification
        clean_answer, clean_citations = process_output(
            answer=crag_res.get("answer", ""),
            citations=crag_res.get("citations", []),
            valid_doc_sources=crag_res.get("valid_doc_sources", set()),
            valid_web_urls=crag_res.get("valid_web_urls", set()),
        )

        latency = time.perf_counter() - start_time

        logger.info(
            "[%s] route=%s source=%s faith_chunks=%d answer=%r",
            sample.id,
            crag_res.get("route", "llm"),
            crag_res.get("source", "llm"),
            len(crag_res.get("chunks") or sample.mock_chunks),
            clean_answer[:200],
        )

        return {
            "answer": clean_answer,
            "source": crag_res.get("source", "llm"),
            "citations": clean_citations,
            "route": crag_res.get("route", "llm"),
            "chunks": crag_res.get("chunks") or sample.mock_chunks,
            "latency_s": latency,
            "blocked": False,
        }
    finally:
        if seeded_source:
            await asyncio.to_thread(_cleanup_eval_documents, session_id, seeded_source)


async def run_evaluation_benchmark(
    samples: Optional[List[EvalSample]] = None,
    category_filter: Optional[str] = None,
    limit: Optional[int] = None,
) -> Dict[str, Any]:
    """Runs evaluation benchmark across samples and calculates aggregate metrics."""
    test_samples = samples or DEFAULT_BENCHMARK_DATASET

    if category_filter:
        test_samples = [s for s in test_samples if s.category == category_filter]

    if limit and limit > 0:
        test_samples = test_samples[:limit]

    logger.info("Starting Cortex Evaluation Benchmark on %d samples...", len(test_samples))

    detailed_results: List[Dict[str, Any]] = []

    for idx, sample in enumerate(test_samples, 1):
        logger.info("[%d/%d] Evaluating sample %s (%s)...", idx, len(test_samples), sample.id, sample.category)
        
        # Execute pipeline
        exec_res = await run_single_pipeline_test(sample)
        
        # Score sample
        scores = await evaluate_sample_async(sample, exec_res)

        record = {
            "id": sample.id,
            "category": sample.category,
            "question": sample.question,
            "expected_route": sample.expected_route,
            "actual_route": exec_res["route"],
            "faithfulness": scores["faithfulness"],
            "answer_relevance": scores["answer_relevance"],
            "guardrail_safety": scores["guardrail_safety"],
            "route_accuracy": scores["route_accuracy"],
            "latency_s": exec_res["latency_s"],
            "answer": exec_res["answer"][:100] + "..." if len(exec_res["answer"]) > 100 else exec_res["answer"],
        }
        detailed_results.append(record)
        await asyncio.sleep(0.5)

    # Compute aggregates
    n = len(detailed_results) or 1
    summary = {
        "faithfulness": sum(r["faithfulness"] for r in detailed_results) / n,
        "answer_relevance": sum(r["answer_relevance"] for r in detailed_results) / n,
        "guardrail_safety": sum(r["guardrail_safety"] for r in detailed_results) / n,
        "route_accuracy": sum(r["route_accuracy"] for r in detailed_results) / n,
        "avg_latency_s": sum(r["latency_s"] for r in detailed_results) / n,
    }

    print_cli_summary(detailed_results, summary)
    report_file = generate_markdown_report(detailed_results, summary)
    logger.info("Report saved to: %s", report_file)

    return {
        "summary": summary,
        "results": detailed_results,
        "report_path": str(report_file),
    }


def main():
    parser = argparse.ArgumentParser(description="Cortex RAG & Guardrails Evaluation Benchmark Runner")
    parser.add_argument("--dataset", type=str, help="Path to custom JSON dataset file")
    parser.add_argument("--category", type=str, help="Filter by test category")
    parser.add_argument("--samples", type=int, default=None, help="Limit number of evaluated samples")
    args = parser.parse_args()

    samples = load_dataset(args.dataset) if args.dataset else None

    asyncio.run(
        run_evaluation_benchmark(
            samples=samples,
            category_filter=args.category,
            limit=args.samples,
        )
    )


if __name__ == "__main__":
    main()
