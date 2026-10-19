from __future__ import annotations

from langchain_groq import ChatGroq
import config


def get_model(model: str, temperature: float) -> ChatGroq:
    """Construct an SDK model; consuming services retain their existing singleton lifecycle."""
    return ChatGroq(model=model, api_key=config.GROQ_API_KEY, temperature=temperature)
