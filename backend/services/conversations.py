from __future__ import annotations

import logging
from typing import List
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
import config
from providers.groq import get_model
from repositories.conversations import ChatMessage, get_messages

logger = logging.getLogger(__name__)
_summarizer_llm = get_model(config.GROQ_FAST_MODEL, 0.3)


def _estimate_tokens(text: str) -> int:
    """Rough token estimate: ~4 characters per token for English text."""
    return max(1, len(text) // 4)


def _format_messages(messages: List[ChatMessage]) -> str:
    """Formats a list of messages into a single conversation string."""
    lines: List[str] = []
    for msg in messages:
        label = "User" if msg.role == "user" else "Assistant"
        lines.append(f"{label}: {msg.content}")
    return "\n".join(lines)


async def _summarize_messages(messages: List[ChatMessage]) -> str:
    """Ask a fast LLM to compress older messages into a concise summary."""
    text = _format_messages(messages)
    system_prompt = (
        "You are a conversation summarizer. Condense the following chat history into 2-3 concise sentences. "
        "Preserve key facts, user preferences, and any unresolved questions. Do not add commentary."
    )
    user_prompt = f"Conversation to summarize:\n\n{text}\n\nSummary:"

    try:
        res = await _summarizer_llm.ainvoke(
            [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
        )
        return str(res.content).strip()
    except Exception as e:
        logger.warning("Conversation summarization failed: %s", e)
        return "[Earlier conversation summary unavailable.]"


async def get_conversation_context(session_id: str) -> str:
    """
    Returns prior conversation context for the LLM.

    - If total estimated tokens are under the budget, return all messages.
    - If over budget, summarize all but the last N messages and keep those verbatim.
    """
    messages = get_messages(session_id)
    if not messages:
        return ""

    total_tokens = sum(_estimate_tokens(m.content) for m in messages)

    # Under budget: include full history
    if total_tokens <= config.MAX_CONVERSATION_TOKENS:
        return _format_messages(messages)

    # Over budget: summarize older messages, keep last N verbatim
    recent = messages[-config.MAX_RECENT_MESSAGES :]
    older = messages[: -config.MAX_RECENT_MESSAGES]

    if older:
        summary = await _summarize_messages(older)
        return (
            f"Summary of earlier conversation:\n{summary}\n\n"
            f"Recent messages:\n{_format_messages(recent)}"
        )

    return _format_messages(recent)


async def get_native_conversation_turns(session_id: str) -> List[BaseMessage]:
    """
    Returns prior conversation turns as native LangChain messages (HumanMessage, AIMessage).
    - If total estimated tokens are within budget, returns all messages as native turns.
    - If over budget, older messages are summarized into a concise SystemMessage context,
      and only the last MAX_RECENT_MESSAGES are kept as verbatim dialogue turns.
    """
    messages = get_messages(session_id)
    if not messages:
        return []

    total_tokens = sum(_estimate_tokens(m.content) for m in messages)

    if total_tokens <= config.MAX_CONVERSATION_TOKENS:
        turns: List[BaseMessage] = []
        for m in messages:
            if m.role == "user":
                turns.append(HumanMessage(content=m.content))
            else:
                turns.append(AIMessage(content=m.content))
        return turns

    # Over budget: summarize older messages, keep the last MAX_RECENT_MESSAGES verbatim
    recent = messages[-config.MAX_RECENT_MESSAGES :]
    older = messages[: -config.MAX_RECENT_MESSAGES]

    turns: List[BaseMessage] = []
    if older:
        summary = await _summarize_messages(older)
        turns.append(
            SystemMessage(content=f"Context from earlier conversation:\n{summary}")
        )

    for m in recent:
        if m.role == "user":
            turns.append(HumanMessage(content=m.content))
        else:
            turns.append(AIMessage(content=m.content))

    return turns


def bounded_history(history: object) -> str:
    if isinstance(history, str):
        return history[-3000:]
    return "\n".join(
        f"{getattr(turn, 'type', 'message')}: {str(getattr(turn, 'content', ''))[:1000]}"
        for turn in (history or [])[-4:]
    )[-3000:]
