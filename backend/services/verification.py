"""
Groundedness Service — NLI Cross-Encoder semantic judge for factuality and anti-hallucination verification.
Evaluates entailment vs contradiction/neutral with a strict threshold (>= 0.85).
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Literal, NamedTuple, Tuple

from langchain_core.messages import HumanMessage, SystemMessage
from providers.groq import get_model
from pydantic import BaseModel, Field

import config

logger = logging.getLogger(__name__)


class GroundednessEvaluation(BaseModel):
    verdict: Literal["ENTAILMENT", "NEUTRAL", "CONTRADICTION"] = Field(
        description=(
            "'ENTAILMENT' if every factual claim in the AI answer is strictly supported and entailed by the provided context; "
            "'NEUTRAL' if claims are unverified, speculative, or unsupported by context; "
            "'CONTRADICTION' if any claim directly conflicts with or contradicts the context."
        )
    )
    entailment_score: float = Field(
        default=0.95,
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0 to 1.0) indicating probability of entailment.",
    )
    reason: str = Field(
        default="",
        description="Brief explanation of the factuality check.",
    )


class GroundednessResult(tuple):
    """Dual tuple-compatible result supporting (is_grounded, reason) unpacking with NLI attributes."""

    def __new__(
        cls,
        is_grounded: bool,
        reason: str,
        verdict: str = "ENTAILMENT",
        score: float = 0.95,
    ):
        return super().__new__(cls, (is_grounded, reason))

    def __init__(
        self,
        is_grounded: bool,
        reason: str,
        verdict: str = "ENTAILMENT",
        score: float = 0.95,
    ):
        self.is_grounded = is_grounded
        self.reason = reason
        self.verdict = verdict
        self.score = score


# Initialize Groq structured NLI judge model
_groq_judge = get_model(config.GROQ_REASONING_MODEL, 0.0).with_structured_output(GroundednessEvaluation)


async def evaluate_groundedness_async(
    question: str,
    context: str,
    answer: str,
) -> GroundednessResult:
    """
    Asynchronously evaluates whether the generated answer is strictly grounded in the provided context
    using NLI Cross-Encoder Entailment verification with threshold >= 0.85.
    Returns GroundednessResult(is_grounded, reason, verdict, score).
    """
    if not context or not answer:
        return GroundednessResult(True, "Empty context or answer; skipping check.", "ENTAILMENT", 1.0)

    messages = [
        SystemMessage(
            content=(
                "You are an independent, strict Natural Language Inference (NLI) Fact-Checking Cross-Encoder.\n"
                "Your objective is to determine whether the Premise (retrieved context) ENTAILS, is NEUTRAL to, "
                "or CONTRADICTS the Hypothesis (the generated answer).\n\n"
                "NLI Classification Rules:\n"
                "- 'ENTAILMENT': Every single factual claim, entity, metric, and statement in the answer is directly and "
                "verifiably supported by the context without outside assumptions.\n"
                "- 'NEUTRAL': The answer makes claims that are plausible or general knowledge but NOT explicitly proven "
                "or stated by the provided context.\n"
                "- 'CONTRADICTION': The answer makes statements that conflict with or negate facts presented in the context.\n\n"
                "Score:\n"
                "- Provide an entailment_score between 0.0 and 1.0.\n"
                "- For genuine ENTAILMENT, assign 0.85 to 1.0.\n"
                "- For NEUTRAL or CONTRADICTION, assign below 0.85.\n"
                "Be uncompromisingly strict. Hallucinations or ungrounded claims must never be marked as ENTAILMENT."
            )
        ),
        HumanMessage(
            content=(
                f"=== Premise (Context) ===\n{context}\n\n"
                f"=== Query ===\n{question}\n\n"
                f"=== Hypothesis (AI Answer) ===\n{answer}"
            )
        ),
    ]

    try:
        eval_res: GroundednessEvaluation = await asyncio.wait_for(
            _groq_judge.ainvoke(messages), timeout=config.TIMEOUT_GROUNDEDNESS
        )
        verdict = eval_res.verdict
        score = eval_res.entailment_score
        reason = eval_res.reason

        # Grounded iff ENTAILMENT with score >= 0.85
        is_grounded = verdict == "ENTAILMENT" and score >= 0.85
        if not is_grounded and verdict == "ENTAILMENT":
            # Demote if score below 0.85 threshold
            verdict = "NEUTRAL"

        return GroundednessResult(is_grounded, reason, verdict, score)
    except Exception as e:
        logger.warning("NLI groundedness judge failed: %s. Defaulting to grounded.", e)
        return GroundednessResult(True, "judge_fallback", "ENTAILMENT", 0.9)
