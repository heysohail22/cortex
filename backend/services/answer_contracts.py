"""Internal contracts for generation and evidence support verification."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class EvidencePassage(BaseModel):
    id: str
    kind: Literal["document", "web"]
    source: str
    text: str
    date: str | None = None


class ClaimSupport(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str
    evidence_ids: list[str]
    source_kind: Literal["document", "web", "mixed"]


class GenerationPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    answer: str
    claims: list[ClaimSupport]


class GenerationResult(BaseModel):
    status: Literal["SUCCESS", "ERROR", "TIMEOUT"]
    answer: str = ""
    claims: list[ClaimSupport] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)
    source: str = "llm"
    error_kind: str | None = None
    provider: str = ""
    model: str = ""
    elapsed_ms: float = 0
    request_made: bool = False
    usage: dict[str, Any] | None = None


class VerificationPayload(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    status: Literal["SUPPORTED", "UNSUPPORTED", "UNKNOWN"]
    checked_claim_indices: list[int]
    unsupported_claim_indices: list[int]
    invalid_evidence_ids: list[str]
    uncovered_claims: list[str]
    reason: str
    confidence: float | None


class VerificationResult(BaseModel):
    status: Literal["SUPPORTED", "UNSUPPORTED", "UNKNOWN", "SKIPPED"]
    unsupported_claim_indices: list[int] = Field(default_factory=list)
    invalid_evidence_ids: list[str] = Field(default_factory=list)
    uncovered_claims: list[str] = Field(default_factory=list)
    reason: str = ""
    confidence: float | None = None
    provider: str = ""
    model: str = ""
    elapsed_ms: float = 0
    request_made: bool = False
    usage: dict[str, Any] | None = None
