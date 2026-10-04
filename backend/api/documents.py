from __future__ import annotations

import asyncio
import logging
import os

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

import config
from guardrails import rate_limit, validate_file_magic
from rag import document_processor, storage_service, vector_store as vs

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["documents"])

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".md", ".rst"}
MAX_FILE_SIZE_MB = 20


class UploadResponse(BaseModel):
    filename: str
    chunks: int
    message: str


class DocumentItem(BaseModel):
    filename: str
    chunks: int = 0


class DocumentListResponse(BaseModel):
    session_id: str
    documents: list[str]
    items: list[DocumentItem] = []


class DeleteResponse(BaseModel):
    message: str


class DocumentUrlResponse(BaseModel):
    filename: str
    url: str



@router.post(
    "/documents/upload",
    response_model=UploadResponse,
    dependencies=[
        Depends(
            rate_limit(
                config.RATE_LIMIT_UPLOAD_REQUESTS,
                config.RATE_LIMIT_UPLOAD_WINDOW,
            )
        )
    ],
)
async def upload_document(
    file: UploadFile = File(...),
    session_id: str = Form(...),
):
    filename = file.filename or "unknown"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    content = await file.read()

    # 1. Size check
    size_mb = len(content) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({size_mb:.1f} MB). Max allowed: {MAX_FILE_SIZE_MB} MB",
        )

    # 2. Layer 1 Ingestion Guard: Magic Bytes & Header Verification
    is_valid_magic, magic_err = validate_file_magic(content, filename)
    if not is_valid_magic:
        logger.warning(
            "File upload rejected for session %s ('%s'): %s",
            session_id,
            filename,
            magic_err,
        )
        raise HTTPException(status_code=400, detail=magic_err)

    try:
        # 1. Offload file parsing, sanitization, and embedding generation to thread pool
        chunks = await asyncio.to_thread(
            document_processor.process_and_index,
            session_id=session_id,
            file_bytes=content,
            filename=filename,
        )
        # 2. Store original raw file in Supabase Storage for preview/download
        await asyncio.to_thread(
            storage_service.upload_file,
            session_id=session_id,
            filename=filename,
            file_bytes=content,
            content_type=file.content_type or "application/octet-stream",
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.exception("Failed to process document '%s'", filename)
        raise HTTPException(status_code=500, detail=f"Processing error: {e}")

    return UploadResponse(
        filename=filename,
        chunks=chunks,
        message=f"Successfully indexed {chunks} chunks from '{filename}'",
    )


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(session_id: str):
    try:
        items = await asyncio.to_thread(vs.list_documents_info, session_id)
        doc_names = [item["filename"] for item in items]
        doc_items = [DocumentItem(filename=item["filename"], chunks=item["chunks"]) for item in items]
        return DocumentListResponse(session_id=session_id, documents=doc_names, items=doc_items)
    except Exception as e:
        logger.warning("Failed to retrieve documents for session '%s': %s", session_id, e)
        return DocumentListResponse(session_id=session_id, documents=[], items=[])


@router.get("/documents/{filename}/url", response_model=DocumentUrlResponse)
async def get_document_url(filename: str, session_id: str):
    """Generate a temporary signed URL to view or download the original uploaded document."""
    url = await asyncio.to_thread(storage_service.get_signed_url, session_id, filename)
    if not url:
        raise HTTPException(
            status_code=404,
            detail=f"Preview/download URL for '{filename}' could not be generated",
        )
    return DocumentUrlResponse(filename=filename, url=url)


@router.delete("/documents/{filename}", response_model=DeleteResponse)
async def delete_document(filename: str, session_id: str):
    has_docs = await asyncio.to_thread(vs.has_documents, session_id)
    if not has_docs:
        raise HTTPException(status_code=404, detail="No documents found for this session")

    # Delete vector chunks and original storage file
    await asyncio.to_thread(vs.delete_document, session_id, filename)
    await asyncio.to_thread(storage_service.delete_file, session_id, filename)
    return DeleteResponse(message=f"Document '{filename}' removed from your session")
