from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: str = Field(..., min_length=1, max_length=128)
    user_id: str | None = Field(None, max_length=128)


class DeleteSessionResponse(BaseModel):
    status: str
    message: str


class ChunkInfo(BaseModel):
    source: str
    text: str
    similarity: float | None = None


class WebResultInfo(BaseModel):
    title: str
    url: str
    content: str


class ChatResponse(BaseModel):
    answer: str
    source: str
    citations: list[str]
    route: str
    suggest_web_search: bool = False
    chunks: list[ChunkInfo] = []
    web_results: list[WebResultInfo] = []
    evidence_status: str | None = None
    retrieval_status: str | None = None
    retrieval_corrections_used: int = 0
    evaluation_result: str | None = None
    evaluation_reason: str | None = None
    is_grounded: bool | None = None
    groundedness_reason: str | None = None
    transformed_query: str | None = None
    nli_verdict: str | None = None
    nli_score: float | None = None
