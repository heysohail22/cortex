from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

import config

logger = logging.getLogger(__name__)


@dataclass
class IndirectInjectionResult:
    is_safe: bool
    risk_score: float
    reason: Optional[str] = None


# ── File Header Signatures (Magic Bytes) ──────────────────────────────────────

_MAGIC_SIGNATURES = {
    ".pdf": [b"%PDF-"],
    ".docx": [b"PK\x03\x04"],
    ".doc": [b"\xd0\xcf\x11\xe0", b"PK\x03\x04"],
}

# Dangerous executable magic bytes (e.g. PE, ELF, Mach-O, scripts)
_EXECUTABLE_MAGIC = [
    b"MZ",                # Windows PE executable / DLL
    b"\x7fELF",           # Linux ELF executable
    b"\xca\xfe\xba\xbe",  # Java class / Mach-O universal binary
    b"\xfe\xed\xfa\xce",  # Mach-O binary
    b"\xfe\xed\xfa\xcf",  # Mach-O binary 64-bit
]

# Zero-width and dangerous invisible Unicode characters
_INVISIBLE_UNICODE_CHARS = re.compile(
    r"[\u200B-\u200D\uFEFF\u00AD\u2060\u200E\u200F\u202A-\u202E]"
)

# Indirect prompt injection indicators embedded in documents
_INDIRECT_INJECTION_PATTERNS = [
    (
        re.compile(
            r"(?i)\b(ignore|disregard|override)\s+(all\s+)?(previous|prior|above|existing)\s+(instructions|prompts|rules|commands|context)\b"
        ),
        "Instruction override directive in document",
    ),
    (
        re.compile(r"(?i)\b(system\s+override|new\s+system\s+instruction)\b"),
        "System override token in document",
    ),
    (
        re.compile(
            r"(?i)\b(when\s+asked|if\s+asked|to\s+the\s+user)\s*,\s*(always\s+)?(say|output|respond|print|reply)\s*:\s*['\"].*?['\"]"
        ),
        "Conditional output hijacking directive",
    ),
    (
        re.compile(
            r"(?i)\b(exfiltrate|send|post|transmit)\s+(this|the|all)\s+(conversation|context|prompt|history)\s+to\b"
        ),
        "Data exfiltration directive in document",
    ),
    (
        re.compile(
            r"(<\|im_start\|>|<\|im_end\|>|\[SYSTEM\]|\[INST\]|<system_override>|---END SYSTEM PROMPT---)"
        ),
        "Raw LLM system boundary token embedded in document",
    ),
]


class IngestionGuard:
    """Validates files and sanitizes document contents against indirect prompt injections."""

    @staticmethod
    def validate_file_magic(file_bytes: bytes, filename: str) -> Tuple[bool, str]:
        """Validates that file content matches its declared extension and has no executable magic."""
        if not getattr(config, "ENABLE_INGESTION_GUARD", True):
            return True, "Ingestion guard disabled"

        if not file_bytes:
            return False, "Uploaded file is empty (0 bytes)."

        # 1. Reject known executable payloads disguised as documents
        for exe_magic in _EXECUTABLE_MAGIC:
            if file_bytes.startswith(exe_magic):
                return (
                    False,
                    "Security violation: Executable or binary payload detected.",
                )

        # 2. Match declared extension against magic bytes
        ext = os.path.splitext(filename)[1].lower()
        if ext in _MAGIC_SIGNATURES:
            expected_magics = _MAGIC_SIGNATURES[ext]
            matched = any(file_bytes.startswith(m) for m in expected_magics)
            if not matched:
                return (
                    False,
                    f"File extension '{ext}' does not match actual file header signature.",
                )

        # 3. For plain text files, ensure valid text decoding
        if ext in (".txt", ".md", ".rst"):
            try:
                # Test first 4KB for text decodability
                sample = file_bytes[:4096]
                sample.decode("utf-8")
            except UnicodeDecodeError:
                try:
                    sample.decode("latin-1")
                except Exception:
                    return (
                        False,
                        "Invalid text encoding: File is not a valid text document.",
                    )

        return True, "File header validation passed."

    @staticmethod
    def sanitize_text(raw_text: str) -> str:
        """Strips invisible zero-width unicode characters and normalizes control codes."""
        if not raw_text:
            return ""

        # Remove zero-width spaces, direction marks, invisible soft-hyphens
        cleaned = _INVISIBLE_UNICODE_CHARS.sub("", raw_text)

        # Remove raw non-printable ASCII control characters except \n, \t, \r
        cleaned = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", cleaned)

        return cleaned.strip()

    @staticmethod
    def scan_chunk_for_indirect_injection(
        chunk_text: str,
    ) -> IndirectInjectionResult:
        """Scans extracted chunk text for indirect prompt injection attempts."""
        if not getattr(config, "ENABLE_INGESTION_GUARD", True):
            return IndirectInjectionResult(is_safe=True, risk_score=0.0)

        for pattern, reason in _INDIRECT_INJECTION_PATTERNS:
            if pattern.search(chunk_text):
                logger.warning("Indirect Prompt Injection Detected in chunk: %s", reason)
                return IndirectInjectionResult(
                    is_safe=False,
                    risk_score=0.9,
                    reason=reason,
                )

        return IndirectInjectionResult(is_safe=True, risk_score=0.0)

    @staticmethod
    def wrap_context_boundary(
        chunk_text: str, source: str, chunk_index: int = 0
    ) -> str:
        """Wraps document text in structural boundary tags to prevent context confusion."""
        escaped_source = source.replace('"', "&quot;")
        return (
            f'<untrusted_document_context source="{escaped_source}" chunk_id="{chunk_index}">\n'
            f"{chunk_text}\n"
            f"</untrusted_document_context>"
        )


# Global singleton helpers
validate_file_magic = IngestionGuard.validate_file_magic
sanitize_text = IngestionGuard.sanitize_text
scan_chunk_for_indirect_injection = IngestionGuard.scan_chunk_for_indirect_injection
wrap_context_boundary = IngestionGuard.wrap_context_boundary
