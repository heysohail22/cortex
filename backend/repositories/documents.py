from __future__ import annotations

import logging
from typing import Any
from repositories.client import _get_client

logger = logging.getLogger(__name__)
TABLE = "document_chunks"
DOCUMENTS_TABLE = "documents"


def has_documents(session_id: str) -> bool:
    client = _get_client()
    response = (
        client.table(TABLE)
        .select("id", count="exact")
        .eq("session_id", session_id)
        .limit(1)
        .execute()
    )
    return (response.count or 0) > 0


def list_document_names(session_id: str) -> list[str]:
    client = _get_client()
    response = (
        client.table(TABLE)
        .select("source")
        .eq("session_id", session_id)
        .execute()
    )
    names = {row["source"] for row in (response.data or []) if row.get("source")}
    return sorted(names)


def list_documents_info(session_id: str) -> list[dict]:
    client = _get_client()
    response = (
        client.table(TABLE)
        .select("source")
        .eq("session_id", session_id)
        .execute()
    )
    counts: dict[str, int] = {}
    for row in (response.data or []):
        src = row.get("source")
        if src:
            counts[src] = counts.get(src, 0) + 1
    return [{"filename": name, "chunks": count} for name, count in sorted(counts.items())]


def save_document_meta(session_id: str, filename: str, topics: str, user_id: str | None = None) -> None:
    """Insert or upsert document metadata and extracted topics into the documents table."""
    try:
        client = _get_client()
        row: dict[str, Any] = {
            "session_id": session_id,
            "filename": filename,
            "topics": topics,
        }
        if user_id:
            row["user_id"] = user_id
        client.table(DOCUMENTS_TABLE).upsert(row, on_conflict="session_id,filename").execute()
        logger.info("Saved metadata for document '%s' in session '%s'", filename, session_id)
    except Exception as e:
        logger.warning("Could not save document metadata to '%s' table: %s", DOCUMENTS_TABLE, e)


def get_document_profiles(session_id: str) -> list[dict]:
    """
    Retrieve document profiles (filename and extracted topics) for a session.
    Falls back gracefully to list_document_names() if the table does not exist or errors.
    """
    client = _get_client()
    try:
        response = (
            client.table(DOCUMENTS_TABLE)
            .select("filename, topics")
            .eq("session_id", session_id)
            .execute()
        )
        data = response.data or []
        if data:
            return [{"filename": row["filename"], "topics": row.get("topics", "")} for row in data]
    except Exception as e:
        logger.warning("Could not fetch from '%s' table: %s. Falling back to chunk sources.", DOCUMENTS_TABLE, e)

    names = list_document_names(session_id)
    return [{"filename": name, "topics": ""} for name in names]


def delete_document(session_id: str, filename: str) -> None:
    client = _get_client()
    client.table(TABLE).delete().eq("session_id", session_id).eq("source", filename).execute()
    try:
        client.table(DOCUMENTS_TABLE).delete().eq("session_id", session_id).eq("filename", filename).execute()
    except Exception as e:
        logger.warning("Could not delete from '%s' table: %s", DOCUMENTS_TABLE, e)


def delete_session_documents(session_id: str) -> None:
    """Delete all document chunks and metadata for a session from Supabase."""
    client = _get_client()
    client.table(TABLE).delete().eq("session_id", session_id).execute()
    try:
        client.table(DOCUMENTS_TABLE).delete().eq("session_id", session_id).execute()
    except Exception as e:
        logger.warning("Could not delete session docs from '%s' table: %s", DOCUMENTS_TABLE, e)
    logger.info("Deleted document chunks and metadata for session %s", session_id)
