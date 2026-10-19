from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

import config

logger = logging.getLogger(__name__)


@dataclass
class PIIRedactResult:
    sanitized_text: str
    has_pii: bool
    detected_entities: Dict[str, int] = field(default_factory=dict)
    entity_mapping: Dict[str, str] = field(default_factory=dict)


# Major Card IIN/BIN Patterns (Visa, Mastercard, Amex, Discover, Diners, JCB)
_CARD_IIN_REGEX = re.compile(
    r"^(?:"
    r"4[0-9]{12}(?:[0-9]{3})?|"                     # Visa (13, 16 digits)
    r"5[1-5][0-9]{14}|"                             # MasterCard (16 digits)
    r"2(?:22[1-9]|2[3-9][0-9]|[3-6][0-9]{2}|7[01][0-9]|720)[0-9]{12}|" # MasterCard 2xxx
    r"3[47][0-9]{13}|"                              # American Express (15 digits)
    r"3(?:0[0-5]|[68][0-9])[0-9]{11}|"              # Diners Club (14 digits)
    r"6(?:011|5[0-9]{2})[0-9]{12}|"                 # Discover (16 digits)
    r"(?:2131|1800|35[0-9]{3})[0-9]{11}"            # JCB (15, 16 digits)
    r")$"
)


def _is_luhn_valid(card_num: str) -> bool:
    """Verifies standard Luhn algorithm (mod 10)."""
    digits = [int(c) for c in card_num if c.isdigit()]
    if len(digits) < 13 or len(digits) > 19:
        return False
    checksum = 0
    reverse_digits = digits[::-1]
    for i, d in enumerate(reverse_digits):
        if i % 2 == 1:
            doubled = d * 2
            checksum += doubled - 9 if doubled > 9 else doubled
        else:
            checksum += d
    return checksum % 10 == 0


def _is_valid_credit_card(raw_candidate: str) -> bool:
    """Validates candidate credit card string using IIN prefix and Luhn checksum."""
    digits = re.sub(r"\D", "", raw_candidate)
    if not _CARD_IIN_REGEX.match(digits):
        return False
    return _is_luhn_valid(digits)


class PIIRedactor:
    """High-speed PII & Secrets Redactor with optional Microsoft Presidio NER support."""

    def __init__(self) -> None:
        self._presidio_analyzer = None
        self._presidio_anonymizer = None
        self._presidio_initialized = False

        # Pre-compiled high-speed regexes
        self._email_regex = re.compile(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
        )
        self._phone_regex = re.compile(
            r"(?<!\d)(?:\+?\d{1,3}[-.\s]?)?(?:\(\d{3}\)|\d{3})[-.\s]?\d{3}[-.\s]?\d{4}(?!\d)"
        )
        self._ssn_regex = re.compile(
            r"\b(?!000|666|9\d{2})\d{3}-(?!00)\d{2}-(?!0000)\d{4}\b"
        )
        self._ip_regex = re.compile(
            r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"
        )
        self._card_candidate_regex = re.compile(
            r"\b(?:\d[ -]*?){13,19}\b"
        )

        # API Keys & Secrets
        self._secret_patterns = [
            ("OPENAI_API_KEY", re.compile(r"sk-(?:proj-)?[a-zA-Z0-9_-]{20,}")),
            ("GROQ_API_KEY", re.compile(r"gsk_[a-zA-Z0-9]{20,}")),
            ("AWS_ACCESS_KEY", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
            ("GITHUB_TOKEN", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{36,}\b")),
            (
                "BEARER_JWT",
                re.compile(
                    r"Bearer\s+[A-Za-z0-9\-_=]+\.[A-Za-z0-9\-_=]+\.?[A-Za-z0-9\-_+/=]*"
                ),
            ),
        ]

    def _init_presidio_if_needed(self) -> None:
        """Lazily initialize Microsoft Presidio if enabled in config."""
        if self._presidio_initialized:
            return
        self._presidio_initialized = True

        if getattr(config, "ENABLE_PRESIDIO_NER", False):
            try:
                from presidio_analyzer import AnalyzerEngine
                from presidio_anonymizer import AnonymizerEngine

                logger.info("Initializing Microsoft Presidio Analyzer Engine...")
                self._presidio_analyzer = AnalyzerEngine()
                self._presidio_anonymizer = AnonymizerEngine()
                logger.info("Microsoft Presidio Engine loaded successfully.")
            except Exception as e:
                logger.warning(
                    "Microsoft Presidio is enabled but failed to load (%s). Falling back to Regex engine.",
                    e,
                )
                self._presidio_analyzer = None
                self._presidio_anonymizer = None

    def redact(self, text: str) -> PIIRedactResult:
        """Synchronously redacts PII and secrets from the text."""
        if not getattr(config, "ENABLE_PII_REDACTION", True):
            return PIIRedactResult(sanitized_text=text, has_pii=False)

        sanitized = text
        entity_counts: Dict[str, int] = {}
        entity_map: Dict[str, str] = {}
        entity_counters: Dict[str, int] = {}

        def _replace_match(entity_type: str, match_text: str) -> str:
            entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
            entity_counters[entity_type] = entity_counters.get(entity_type, 0) + 1
            placeholder = f"<{entity_type}_{entity_counters[entity_type]}>"
            entity_map[placeholder] = match_text
            return placeholder

        # 1. API Keys & Secrets
        for secret_name, secret_re in self._secret_patterns:
            matches = list(secret_re.finditer(sanitized))
            for m in reversed(matches):
                val = m.group(0)
                placeholder = _replace_match(secret_name, val)
                sanitized = sanitized[: m.start()] + placeholder + sanitized[m.end() :]

        # 2. Credit Cards (with IIN Prefix + Luhn check)
        card_matches = list(self._card_candidate_regex.finditer(sanitized))
        for m in reversed(card_matches):
            raw_card = m.group(0)
            if _is_valid_credit_card(raw_card):
                placeholder = _replace_match("CREDIT_CARD", raw_card)
                sanitized = (
                    sanitized[: m.start()] + placeholder + sanitized[m.end() :]
                )

        # 3. SSN
        ssn_matches = list(self._ssn_regex.finditer(sanitized))
        for m in reversed(ssn_matches):
            val = m.group(0)
            placeholder = _replace_match("US_SSN", val)
            sanitized = sanitized[: m.start()] + placeholder + sanitized[m.end() :]

        # 4. Email Addresses
        email_matches = list(self._email_regex.finditer(sanitized))
        for m in reversed(email_matches):
            val = m.group(0)
            placeholder = _replace_match("EMAIL_ADDRESS", val)
            sanitized = sanitized[: m.start()] + placeholder + sanitized[m.end() :]

        # 5. Phone Numbers
        phone_matches = list(self._phone_regex.finditer(sanitized))
        for m in reversed(phone_matches):
            val = m.group(0)
            # Avoid single short digit strings
            if len(re.sub(r"\D", "", val)) >= 10:
                placeholder = _replace_match("PHONE_NUMBER", val)
                sanitized = (
                    sanitized[: m.start()] + placeholder + sanitized[m.end() :]
                )

        # 6. IP Addresses
        ip_matches = list(self._ip_regex.finditer(sanitized))
        for m in reversed(ip_matches):
            val = m.group(0)
            # Ignore standard localhost or zero IPs if desired, or mask all
            if val not in ("127.0.0.1", "0.0.0.0"):
                placeholder = _replace_match("IP_ADDRESS", val)
                sanitized = (
                    sanitized[: m.start()] + placeholder + sanitized[m.end() :]
                )

        # 7. Microsoft Presidio NER (if loaded)
        self._init_presidio_if_needed()
        if self._presidio_analyzer and self._presidio_anonymizer:
            try:
                results = self._presidio_analyzer.analyze(
                    text=sanitized,
                    entities=["PERSON", "LOCATION", "ORGANIZATION"],
                    language="en",
                )
                if results:
                    anonymized_res = self._presidio_anonymizer.anonymize(
                        text=sanitized, analyzer_results=results
                    )
                    sanitized = anonymized_res.text
                    for r in results:
                        entity_counts[r.entity_type] = (
                            entity_counts.get(r.entity_type, 0) + 1
                        )
            except Exception as e:
                logger.warning("Presidio NER execution error: %s", e)

        has_pii = len(entity_counts) > 0
        if has_pii:
            logger.info("PII Redacted: %s", entity_counts)

        return PIIRedactResult(
            sanitized_text=sanitized,
            has_pii=has_pii,
            detected_entities=entity_counts,
            entity_mapping=entity_map,
        )

    async def redact_async(self, text: str) -> PIIRedactResult:
        """Asynchronously runs PII redaction without blocking event loop."""
        return await asyncio.to_thread(self.redact, text)


# Global singleton
_pii_redactor = PIIRedactor()


async def redact_pii_async(text: str) -> PIIRedactResult:
    return await _pii_redactor.redact_async(text)


def redact_pii(text: str) -> PIIRedactResult:
    return _pii_redactor.redact(text)
