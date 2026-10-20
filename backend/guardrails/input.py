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


# Known injection and jailbreak patterns

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
    """Local pattern-based prompt injection and jailbreak detector."""


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


    async def check_async(self, text: str) -> PromptGuardResult:
        """Check known patterns; Jev performs a separate safety assessment in routing."""
        if not getattr(config, "ENABLE_PROMPT_GUARD", True):
            return PromptGuardResult(is_safe=True, risk_score=0.0)

        # Check known patterns without a model call.
        heuristic_res = self.check_heuristics(text)
        if heuristic_res:
            logger.warning(
                "Prompt Guard [Heuristic Block]: %s (Reason: %s)",
                heuristic_res.violation_type,
                heuristic_res.reason,
            )
            return heuristic_res

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
