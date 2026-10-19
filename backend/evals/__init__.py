"""
Cortex Evaluation Framework — Automated benchmarks for RAG quality, groundedness, and guardrails.
"""
from __future__ import annotations

from evals.datasets.samples import (
    DEFAULT_BENCHMARK_DATASET,
    EvalSample,
    load_dataset,
    save_dataset,
)
from evals.metrics.scoring import (
    evaluate_answer_relevance_score,
    evaluate_faithfulness_score,
    evaluate_guardrail_safety,
    evaluate_sample_async,
)
from evals.report import generate_markdown_report, print_cli_summary
def __getattr__(name):
    if name in {"run_evaluation_benchmark", "run_single_pipeline_test"}:
        from evals import runner
        return getattr(runner, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    "DEFAULT_BENCHMARK_DATASET",
    "EvalSample",
    "load_dataset",
    "save_dataset",
    "evaluate_answer_relevance_score",
    "evaluate_faithfulness_score",
    "evaluate_guardrail_safety",
    "evaluate_sample_async",
    "generate_markdown_report",
    "print_cli_summary",
    "run_evaluation_benchmark",
    "run_single_pipeline_test",
]
