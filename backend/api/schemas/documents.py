from __future__ import annotations

from pydantic import BaseModel, Field


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
