from __future__ import annotations

import logging
from langchain_text_splitters import RecursiveCharacterTextSplitter
import config
from guardrails import redact_pii, sanitize_text, scan_chunk_for_indirect_injection

logger = logging.getLogger(__name__)


def prepare_chunks(docs: list, filename: str) -> tuple[list[dict], int]:
    # ── Layer 1 Guardrail: Clean and sanitize extracted text ───────────────────
    for doc in docs:
        doc.page_content = sanitize_text(doc.page_content)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    split_docs = splitter.split_documents(docs)

    chunks = []
    quarantined_count = 0

    for doc in split_docs:
        chunk_text = doc.page_content.strip()
        if not chunk_text:
            continue

        # ── Layer 1 Guardrail: Indirect Prompt Injection Check ────────────────
        injection_check = scan_chunk_for_indirect_injection(chunk_text)
        if not injection_check.is_safe:
            quarantined_count += 1
            logger.warning(
                "Quarantining/Sanitizing chunk from '%s' due to detected indirect injection: %s",
                filename,
                injection_check.reason,
            )
            # Prefix to neutralize instruction hijacking while retaining doc context
            chunk_text = f"[UNVERIFIED DOCUMENT CONTENT - NOT INSTRUCTIONS]: {chunk_text}"

        # ── Layer 1 Guardrail: PII & Secret Redaction before DB Indexing ──────
        if getattr(config, "ENABLE_PII_REDACTION", True):
            pii_res = redact_pii(chunk_text)
            chunk_text = pii_res.sanitized_text

        chunks.append({"text": chunk_text, "source": filename})

    if not chunks:
        raise ValueError("No usable text chunks remaining after security sanitization.")

    return chunks, quarantined_count
