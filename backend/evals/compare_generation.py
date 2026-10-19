"""Opt-in paid model comparison on fixed synthetic evidence, with no retrieval writes."""
from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import statistics
import time


def estimate_cost(attempts: list[dict], rates: dict) -> float | None:
    """Rates must be supplied for actual model IDs; missing usage is never free."""
    total = 0.0
    for attempt in attempts:
        if attempt.get("request_made") is False:
            continue
        usage = attempt.get("usage")
        rate = rates.get(f"{attempt.get('provider')}:{attempt.get('model')}")
        if not usage or not rate:
            return None
        incoming = usage.get("prompt_tokens", usage.get("prompt_token_count"))
        outgoing = usage.get("completion_tokens")
        if outgoing is None and "candidates_token_count" in usage:
            outgoing = (usage.get("candidates_token_count") or 0) + (usage.get("thoughts_token_count") or 0)
        cached = (usage.get("prompt_tokens_details") or {}).get("cached_tokens", usage.get("cached_content_token_count", 0)) or 0
        if incoming is None or outgoing is None or cached > incoming:
            return None
        cache_rate = rate.get("cached_input_per_million")
        if cached and cache_rate is None:
            return None
        values = [rate["input_per_million"], rate["output_per_million"], cache_rate or 0, incoming, outgoing, cached]
        if any(not math.isfinite(v) or v < 0 for v in values):
            raise ValueError("Invalid token counts or rates")
        total += ((incoming-cached)*rate["input_per_million"] + outgoing*rate["output_per_million"] + cached*(cache_rate or 0))/1_000_000
    return total


async def compare(cases: list[dict], candidates: list[str], rates: dict) -> list[dict]:
    import config
    from services.generation import build_snapshot
    from workflows.crag.nodes.generation import generate_node, direct_answer_node, strict_constrained_generator_node
    from workflows.crag.nodes.verification import groundedness_check_node, safe_fallback_node
    from workflows.crag.edges import decide_after_groundedness
    from providers.groq import close_answer_client as close_groq
    from providers.gemini import close_answer_client as close_gemini

    old = config.GENERATION_PROVIDER, config.GENERATION_MODEL
    results = []
    try:
        for case in cases:
            snapshot, truncated = build_snapshot(case["chunks"], case["web_results"])
            for candidate in candidates:
                config.GENERATION_PROVIDER, config.GENERATION_MODEL = candidate.split(":", 1)
                state = {"question": case["question"], "route": "web_search" if case["source"] == "web_search" else "rag",
                         "chunks": case["chunks"], "web_results": case["web_results"],
                         "evidence_status": "PARTIAL" if truncated else case.get("evidence_status"),
                         "generation_snapshot": [p.model_dump() for p in snapshot], "snapshot_truncated": truncated,
                         "missing_requirements": "Evidence was budget-limited." if truncated else "",
                         "answer_repairs_used": 0, "answer_deadline": time.monotonic()+config.TIMEOUT_ANSWER_STAGE}
                start = time.monotonic()
                if case["source"] == "llm":
                    state = await direct_answer_node(state)
                else:
                    state = await groundedness_check_node(await generate_node(state))
                    if decide_after_groundedness(state) == "strict_retry_node":
                        state = await groundedness_check_node(await strict_constrained_generator_node(state))
                    if decide_after_groundedness(state) == "safe_fallback_node":
                        state = await safe_fallback_node(state)
                attempts = state.get("answer_attempts", [])
                results.append({"case_id": case["id"], "candidate": candidate,
                                "elapsed_ms": round((time.monotonic()-start)*1000, 2),
                                "answer": state.get("answer"), "citations": state.get("citations", []),
                                "verification_status": state.get("verification_status"), "repairs": state.get("answer_repairs_used", 0),
                                "attempts": attempts, "estimated_cost_usd": estimate_cost(attempts, rates),
                                "reference_answer": case["reference_answer"], "human_review": None})
    finally:
        config.GENERATION_PROVIDER, config.GENERATION_MODEL = old
        await asyncio.gather(close_groq(), close_gemini())
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", action="append", required=True, help="Repeat provider:model, e.g. groq:openai/gpt-oss-120b")
    parser.add_argument("--dataset", type=Path, default=Path(__file__).parent/"datasets/generation_comparison.json")
    parser.add_argument("--limit", type=int, default=32)
    parser.add_argument("--rates-json", type=Path, help="Actual provider:model IDs -> input_per_million, output_per_million, optional cached_input_per_million")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--dry-run", action="store_true", help="Validate inputs without any model requests")
    args = parser.parse_args()
    cases = json.loads(args.dataset.read_text())[:args.limit]
    if not cases or args.limit <= 0:
        parser.error("A positive case count is required")
    for candidate in args.candidate:
        if ":" not in candidate or candidate.split(":",1)[0] not in ("groq", "gemini") or not candidate.split(":",1)[1]:
            parser.error("Candidates must be groq:model or gemini:model")
    if args.dry_run:
        print(json.dumps({"cases": len(cases), "candidates": args.candidate, "model_requests": 0}))
        return
    if args.output and args.output.exists():
        parser.error("Output already exists; choose a new path")
    rates = json.loads(args.rates_json.read_text()) if args.rates_json else {}
    if not isinstance(rates, dict):
        parser.error("Rates must be a model-keyed object")
    for rate in rates.values():
        if not isinstance(rate, dict) or not {"input_per_million", "output_per_million"} <= set(rate):
            parser.error("Each model rate requires input_per_million and output_per_million")
        if any(not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0 for value in rate.values()):
            parser.error("Rates must be finite nonnegative numbers")
    results = asyncio.run(compare(cases, args.candidate, rates))
    summary = {}
    for candidate in args.candidate:
        rows = [r for r in results if r["candidate"] == candidate]
        latencies = sorted(r["elapsed_ms"] for r in rows)
        summary[candidate] = {"median_ms": statistics.median(latencies), "p95_ms": latencies[math.ceil(len(latencies)*0.95)-1],
                              "repairs": sum(r["repairs"] for r in rows),
                              "unknown": sum(r["verification_status"] == "UNKNOWN" for r in rows),
                              "estimated_cost_usd": sum(r["estimated_cost_usd"] for r in rows) if all(r["estimated_cost_usd"] is not None for r in rows) else None}
    output = args.output or Path(__file__).parent/"reports"/f"generation_comparison_{datetime.now(timezone.utc):%Y%m%d_%H%M%S}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"summary": summary, "results": results, "notice": "Synthetic reference expectations require human review; judge verdicts are not ground truth."}, indent=2)+"\n")
    print(output)


if __name__ == "__main__":
    main()
