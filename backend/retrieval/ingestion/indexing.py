from __future__ import annotations

import logging
from retrieval import vector_store as vs
from repositories import documents
from retrieval.ingestion.parsing import parse_document
from retrieval.ingestion.chunking import prepare_chunks

logger = logging.getLogger(__name__)


def process_and_index(session_id: str, file_bytes: bytes, filename: str) -> int:
    docs, topics = parse_document(file_bytes, filename)
    chunks, quarantined_count = prepare_chunks(docs, filename)
    vs.add_documents(session_id, chunks)
    documents.save_document_meta(session_id=session_id, filename=filename, topics=topics)
    logger.info(
        "Indexed %d chunks for '%s' with topics '%s' (session: %s, flagged/quarantined: %d)",
        len(chunks),
        filename,
        topics,
        session_id,
        quarantined_count,
    )
    return len(chunks)
