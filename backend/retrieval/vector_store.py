from __future__ import annotations

import config
from repositories.client import _get_client
from retrieval import embeddings as emb

TABLE = "document_chunks"


def add_documents(session_id: str, chunks: list[dict]) -> None:
    client = _get_client()

    texts = [c["text"] for c in chunks]
    sources = [c["source"] for c in chunks]

    # Step 1: Generate embeddings in the cloud (zero local RAM/CPU usage)
    vectors = emb.embed_texts(texts)

    # Step 2: Build rows for bulk insert
    rows = [
        {
            "session_id": session_id,
            "content": text,
            "source": source,
            "embedding": vector,
        }
        for text, source, vector in zip(texts, sources, vectors)
    ]

    client.table(TABLE).insert(rows).execute()


def similarity_search(session_id: str, query: str, k: int = config.TOP_K_RESULTS) -> list[dict]:
    client = _get_client()
    query_vector = emb.embed_query(query)

    try:
        match_count = int(k)
    except (TypeError, ValueError):
        match_count = 5

    response = client.rpc(
        "match_document_chunks",
        {
            "query_embedding": query_vector,
            "match_threshold": config.SIMILARITY_THRESHOLD,
            "match_count": match_count,
            "filter_session_id": session_id,
        },
    ).execute()

    return [
        {
            "text": row["content"],
            "source": row["source"],
        }
        for row in (response.data or [])
    ]
