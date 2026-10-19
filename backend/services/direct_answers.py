"""
LLM Service — Direct conversational AI response service.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict

from langchain_core.messages import HumanMessage, SystemMessage
from providers.groq import get_model

import config

logger = logging.getLogger(__name__)


# Initialize Groq 20b model
_groq_direct_llm = get_model(config.GROQ_FAST_MODEL, 0.7)

SYSTEM_PROMPT = """You are Cortex, a helpful and knowledgeable AI assistant.
You answer questions clearly and concisely based on your training knowledge.
If you're unsure, say so honestly rather than guessing.
Format your answers in a readable way using markdown where helpful."""


def _clean_response(text: str) -> str:
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    return cleaned if cleaned else text.strip()


async def run_llm_async(question: str) -> Dict[str, Any]:
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=question),
    ]

    answer = ""
    try:
        response = await _groq_direct_llm.ainvoke(messages)
        answer = _clean_response(str(response.content))
    except Exception as e:
        logger.error("Groq 20b direct LLM failed: %s.", e)

    if not answer:
        answer = "I am Cortex, an AI assistant. How can I help you today?"

    return {
        "answer": answer,
        "source": "llm",
        "citations": [],
    }


def run_llm(question: str) -> Dict[str, Any]:
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=question),
    ]

    answer = ""
    try:
        response = _groq_direct_llm.invoke(messages)
        answer = _clean_response(str(response.content))
    except Exception as e:
        logger.error("Groq 20b direct LLM failed: %s.", e)

    if not answer:
        answer = "I am Cortex, an AI assistant. How can I help you today?"

    return {
        "answer": answer,
        "source": "llm",
        "citations": [],
    }
