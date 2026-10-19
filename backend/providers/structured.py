"""Provider-independent transport response, without application verdicts."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class StructuredResponse:
    data: dict[str, Any]
    model: str
    usage: dict[str, Any] | None = None


class InvalidProviderOutput(ValueError):
    """A completed request returned incomplete or malformed output."""

    def __init__(self, message="Invalid output", *, model=None, usage=None):
        super().__init__(message)
        self.model = model
        self.usage = usage


async def generate_structured(provider: str, **kwargs) -> StructuredResponse:
    if provider == "groq":
        from providers.groq import generate_structured as invoke
    elif provider == "gemini":
        from providers.gemini import generate_structured as invoke
    else:
        raise ValueError("Unsupported answer provider")
    return await invoke(**kwargs)
