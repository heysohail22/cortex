from __future__ import annotations

from unittest.mock import patch

import pytest

from retrieval.ingestion.indexing import process_and_index
from retrieval.ingestion.parsing import parse_document


def test_text_ingestion_preserves_scope_topics_and_redaction():
    content = b"# Refund policy\nRefund requests must arrive within thirty days. Contact alice@example.com."
    with patch("retrieval.ingestion.indexing.vs.add_documents") as index, \
         patch("retrieval.ingestion.indexing.documents.save_document_meta") as metadata:
        count = process_and_index("session-ingestion", content, "refund.md")
    session, chunks = index.call_args.args
    assert session == "session-ingestion"
    assert count == len(chunks) and count > 0
    assert all(c["source"] == "refund.md" for c in chunks)
    assert "thirty days" in " ".join(c["text"] for c in chunks)
    assert "alice@example.com" not in " ".join(c["text"] for c in chunks)
    assert metadata.call_args.kwargs["session_id"] == session
    assert "Refund policy" in metadata.call_args.kwargs["topics"]


def test_parser_removes_temporary_file_on_loader_failure():
    from pathlib import Path
    captured_paths = []

    def fail(path, **kwargs):
        captured_paths.append(Path(path))
        assert Path(path).exists()
        raise RuntimeError("parser unavailable")

    with patch("retrieval.ingestion.parsing.TextLoader", side_effect=fail):
        with pytest.raises(RuntimeError, match="parser unavailable"):
            parse_document(b"test", "test.txt")
    assert captured_paths and not captured_paths[0].exists()
