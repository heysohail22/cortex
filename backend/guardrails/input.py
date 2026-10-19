from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass
from typing import Optional

import config

logger = logging.getLogger(__name__)


@dataclass
class PromptGuardResult:
    is_safe: bool
    risk_score: float  # 0.0 to 1.0
    violation_type: Optional[str] = None
    reason: Optional[str] = None


# ── Fast Heuristic Signatures (Tier 1: 0ms execution) ─────────────────────────

_INJECTION_PATTERNS = [
    (
        r"(?i)\b(ignore|disregard|forget|override)\s+(all\s+)?(previous|prior|above|existing)\s+(instructions|prompts|rules|commands|context)\b",
        "DIRECT_INJECTION",
        "Attempted to override system instructions",
    ),
    (
        r"(?i)\b(system\s+override|new\s+system\s+prompt|reset\s+all\s+instructions)\b",
        "DIRECT_INJECTION",
        "Attempted to reset system prompt boundary",
    ),
    (
        r"(?i)\b(repeat|print|output|show|reveal|echo)\s+(your\s+|the\s+)?(secret\s+)?(system\s+prompt|initial\s+instructions|core\s+(prompt|instructions)|base\s+(prompt|instructions))\b",
        "SYSTEM_PROMPT_LEAK",
        "Attempted to exfiltrate system instructions",
    ),
    (
        r"(?i)\b(what\s+(is|are)\s+(your\s+)?(secret\s+)?(system\s+prompt|core\s+instructions|secret\s+instructions|base\s+prompt))\b",
        "SYSTEM_PROMPT_LEAK",
        "Attempted to exfiltrate system instructions",
    ),
    (
        r"(?i)\b(dan\s+mode|do\s+anything\s+now|developer\s+mode\s+enabled|jailbreak(ed)?|unfiltered\s+ai|anti-censor)\b",
        "JAILBREAK",
        "Attempted jailbreak persona activation",
    ),
    (
        r"(?i)\b(act\s+as\s+(an?\s+)?unrestricted|simulate\s+an\s+unfiltered|bypass\s+all\s+safety\s+filters)\b",
        "JAILBREAK",
        "Attempted roleplay safety bypass",
    ),
    (
        r"(<\|im_start\|>|<\|im_end\|>|\[SYSTEM\]|\[INST\]|<system>|<\/system>|---BEGIN INSTRUCTION---|---END SYSTEM PROMPT---)",
        "DIRECT_INJECTION",
        "Detected raw LLM token delimiter injection",
    ),
]

_COMPILED_PATTERNS = [
    (re.compile(pattern), vtype, reason)
    for pattern, vtype, reason in _INJECTION_PATTERNS
]


class PromptGuard:
    """Multi-tiered Prompt Injection & Jailbreak Detector."""

    def __init__(self) -> None:
        self._hf_pipeline = None
        self._hf_initialized = False

    def _init_local_model_if_needed(self) -> None:
        """Lazily initialize local Hugging Face Prompt Guard model if requested and available."""
        if self._hf_initialized:
            return
        self._hf_initialized = True

        if getattr(config, "USE_LOCAL_PROMPT_GUARD_MODEL", False):
            try:
                import importlib
                transformers_pkg = importlib.import_module("transformers")
                pipeline_fn = getattr(transformers_pkg, "pipeline")

                model_name = getattr(
                    config, "PROMPT_GUARD_MODEL", "meta-llama/Prompt-Guard-86M"
                )
                logger.info("Loading local Prompt Guard model: %s", model_name)
                self._hf_pipeline = pipeline_fn("text-classification", model=model_name)
            except Exception as e:
                logger.warning(
                    "Could not load local Prompt Guard model (%s). Using heuristics + Groq guard: %s",
                    getattr(config, "PROMPT_GUARD_MODEL", "meta-llama/Prompt-Guard-86M"),
                    e,
                )
                self._hf_pipeline = None

    def check_heuristics(self, text: str) -> Optional[PromptGuardResult]:
        """Runs fast regex pattern matching against known injection/jailbreak signatures."""
        for pattern, vtype, reason in _COMPILED_PATTERNS:
            if pattern.search(text):
                return PromptGuardResult(
                    is_safe=False,
                    risk_score=1.0,
                    violation_type=vtype,
                    reason=reason,
                )
        return None

    def check_local_model(self, text: str) -> Optional[PromptGuardResult]:
        """Evaluates prompt using local Prompt Guard classifier if loaded."""
        self._init_local_model_if_needed()
        if not self._hf_pipeline:
            return None

        try:
            results = self._hf_pipeline(text[:2000])  # Cap length for classifier
            top = results[0]
            label = top.get("label", "").upper()
            score = top.get("score", 0.0)

            # Llama-Prompt-Guard outputs: 'BENIGN', 'INJECTION', 'JAILBREAK'
            if label in ("INJECTION", "JAILBREAK") and score >= getattr(
                config, "PROMPT_GUARD_THRESHOLD", 0.5
            ):
                return PromptGuardResult(
                    is_safe=False,
                    risk_score=score,
                    violation_type=label,
                    reason=f"Model classified input as {label} with confidence {score:.2f}",
                )
            return PromptGuardResult(is_safe=True, risk_score=1.0 - score)
        except Exception as e:
            logger.warning("Local Prompt Guard model evaluation error: %s", e)
            return None

    async def check_async(self, text: str) -> PromptGuardResult:
        """Full async inspection pipeline: Heuristics -> Local Model -> Safe."""
        if not getattr(config, "ENABLE_PROMPT_GUARD", True):
            return PromptGuardResult(is_safe=True, risk_score=0.0)

        # 1. Tier 1: 0ms Heuristic check
        heuristic_res = self.check_heuristics(text)
        if heuristic_res:
            logger.warning(
                "Prompt Guard [Heuristic Block]: %s (Reason: %s)",
                heuristic_res.violation_type,
                heuristic_res.reason,
            )
            return heuristic_res

        # 2. Tier 2: Local ML Model (Prompt Guard 86M/22M) if enabled
        if getattr(config, "USE_LOCAL_PROMPT_GUARD_MODEL", False):
            model_res = await asyncio.to_thread(self.check_local_model, text)
            if model_res and not model_res.is_safe:
                logger.warning(
                    "Prompt Guard [Model Block]: %s (Score: %.2f)",
                    model_res.violation_type,
                    model_res.risk_score,
                )
                return model_res

        return PromptGuardResult(is_safe=True, risk_score=0.0)

    def check(self, text: str) -> PromptGuardResult:
        """Synchronous check."""
        return asyncio.run(self.check_async(text))


# Singleton instance
_prompt_guard = PromptGuard()


async def check_prompt_async(text: str) -> PromptGuardResult:
    return await _prompt_guard.check_async(text)


def check_prompt(text: str) -> PromptGuardResult:
    return _prompt_guard.check(text)
