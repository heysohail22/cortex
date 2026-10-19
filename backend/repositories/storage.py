from __future__ import annotations

import logging
from functools import lru_cache
from typing import List, Optional

from supabase import Client

import config
from repositories.client import _get_client

logger = logging.getLogger(__name__)

BUCKET_NAME = "documents"


def ensure_bucket_exists() -> None:
    """Ensure the documents storage bucket exists in Supabase."""
    try:
        client: Client = _get_client()
        existing = [b.name for b in client.storage.list_buckets()]
        if BUCKET_NAME not in existing:
            client.storage.create_bucket(BUCKET_NAME, options={"public": False})
            logger.info("Created Supabase storage bucket '%s'", BUCKET_NAME)
    except Exception as e:
        logger.warning("Could not verify/create storage bucket '%s': %s", BUCKET_NAME, e)


def upload_file(
    session_id: str,
    filename: str,
    file_bytes: bytes,
    content_type: str = "application/octet-stream",
) -> Optional[str]:
    """
    Upload raw file to Supabase storage bucket under 'session_id/filename'.
    Returns the storage path or None if upload failed.
    """
    try:
        ensure_bucket_exists()
        client: Client = _get_client()
        file_path = f"{session_id}/{filename}"
        
        client.storage.from_(BUCKET_NAME).upload(
            path=file_path,
            file=file_bytes,
            file_options={"content-type": content_type, "upsert": "true"},
        )
        logger.info("Uploaded raw file to storage: %s/%s", BUCKET_NAME, file_path)
        return file_path
    except Exception as e:
        logger.warning("Failed to upload '%s' to storage bucket: %s", filename, e)
        return None


def get_signed_url(session_id: str, filename: str, expires_in: int = 3600) -> Optional[str]:
    """Generate a temporary signed URL to view/download the original file."""
    try:
        client: Client = _get_client()
        file_path = f"{session_id}/{filename}"
        res = client.storage.from_(BUCKET_NAME).create_signed_url(file_path, expires_in)
        if isinstance(res, dict):
            return res.get("signedURL") or res.get("signedUrl")
        return None
    except Exception as e:
        logger.warning("Failed to create signed URL for '%s': %s", filename, e)
        return None


def delete_file(session_id: str, filename: str) -> None:
    """Delete a raw file from Supabase storage."""
    try:
        client: Client = _get_client()
        file_path = f"{session_id}/{filename}"
        client.storage.from_(BUCKET_NAME).remove([file_path])
        logger.info("Deleted file from storage: %s/%s", BUCKET_NAME, file_path)
    except Exception as e:
        logger.warning("Failed to delete '%s' from storage: %s", filename, e)


def delete_session_files(session_id: str) -> None:
    """Delete all raw files stored under a session folder."""
    try:
        client: Client = _get_client()
        files = client.storage.from_(BUCKET_NAME).list(session_id)
        if files:
            paths = [f"{session_id}/{f['name']}" for f in files if f.get("name")]
            if paths:
                client.storage.from_(BUCKET_NAME).remove(paths)
                logger.info("Deleted %d files from storage for session %s", len(paths), session_id)
    except Exception as e:
        logger.warning("Failed to delete storage files for session %s: %s", session_id, e)
