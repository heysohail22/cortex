from __future__ import annotations

import hashlib
import config


def merge_candidates(chunks: list[dict]) -> list[dict]:
    """Prefer persistent identity; otherwise hash source and normalized content."""
    result, seen = [], set()
    for chunk in chunks:
        text = str(chunk.get("text") or "").strip()
        if not text:
            continue
        source = str(chunk.get("source") or "Unknown")
        identity = str(chunk.get("id") or hashlib.sha256((source + "\0" + " ".join(text.split())).encode()).hexdigest())
        identity = str(chunk.get("evidence_id") or hashlib.sha256((source + "\0" + identity).encode()).hexdigest()[:24])
        if identity not in seen:
            result.append({**chunk, "text": text, "source": source, "evidence_id": identity})
            seen.add(identity)
    return result


def bounded_candidates(chunks: list[dict]) -> tuple[list[dict], bool]:
    budget = min(config.MAX_EVIDENCE_CONTEXT_CHARS, config.MAX_DOC_CONTEXT_CHARS - 1000, config.MAX_HYBRID_DOC_CHARS - 1000)
    if budget <= 0 or config.MAX_EVIDENCE_CANDIDATES <= 0 or config.MAX_EVIDENCE_PASSAGE_CHARS <= 0:
        raise ValueError("Invalid evidence budget")
    candidates = merge_candidates(chunks)
    result, truncated = [], False
    for chunk in candidates:
        if len(result) >= config.MAX_EVIDENCE_CANDIDATES or budget <= 0:
            truncated = True
            break
        overhead = len(chunk["source"]) + 100
        if budget <= overhead:
            truncated = True
            break
        text = chunk["text"][:min(budget - overhead, config.MAX_EVIDENCE_PASSAGE_CHARS)]
        truncated |= len(text) != len(chunk["text"])
        # Downstream generation sees precisely the assessed text, never the original tail.
        result.append({**chunk, "text": text})
        budget -= len(text) + overhead
    return result, truncated
