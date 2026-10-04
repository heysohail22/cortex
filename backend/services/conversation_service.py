"""
Conversation Service — Stores session history, summarizes old messages, and keeps
the most recent N messages verbatim so the LLM never loses short-term context.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_groq import ChatGroq

import config
from rag import vector_store as vs

logger = logging.getLogger(__name__)

# Fast/cheap model for summarization so we don't burn reasoning-model quota
_summarizer_llm = ChatGroq(
    model=config.GROQ_FAST_MODEL,
    api_key=config.GROQ_API_KEY,
    temperature=0.3,
)


@dataclass
class ChatMessage:
    role: str
    content: str


def _get_client():
    """Reuse the singleton Supabase client from the vector store module."""
    return vs._get_client()


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


CHAT_HISTORY_TABLE = "chat_history"


def save_turn(session_id: str, user_message: str, assistant_message: str) -> None:
    """Persist a dialogue turn (user question + assistant response) to chat_history in Supabase."""
    try:
        client = _get_client()
        client.table(CHAT_HISTORY_TABLE).insert(
            {
                "session_id": session_id,
                "user_message": user_message,
                "assistant_message": assistant_message,
            }
        ).execute()
    except Exception as e:
        logger.warning("Failed to save chat history turn for %s: %s", session_id, e)


def get_messages(session_id: str) -> List[ChatMessage]:
    """Fetch all messages for a session from chat_history, ordered by time."""
    try:
        client = _get_client()
        response = (
            client.table(CHAT_HISTORY_TABLE)
            .select("user_message,assistant_message,created_at")
            .eq("session_id", session_id)
            .order("created_at")
            .execute()
        )
        messages: List[ChatMessage] = []
        for row in (response.data or []):
            u_msg = row.get("user_message")
            a_msg = row.get("assistant_message")
            if u_msg:
                messages.append(ChatMessage(role="user", content=u_msg))
            if a_msg:
                messages.append(ChatMessage(role="assistant", content=a_msg))
        return messages
    except Exception as e:
        logger.warning("Failed to fetch chat history for %s: %s", session_id, e)
        return []


def delete_conversation(session_id: str) -> None:
    """Delete all chat history turns for a session from Supabase."""
    try:
        client = _get_client()
        client.table(CHAT_HISTORY_TABLE).delete().eq("session_id", session_id).execute()
        logger.info("Deleted chat history for session %s", session_id)
    except Exception as e:
        logger.warning("Failed to delete chat history for %s: %s", session_id, e)
        raise


def get_all_sessions_summary() -> list[dict]:
    """Fetch all unique conversation sessions from chat_history with their user & assistant messages."""
    try:
        client = _get_client()
        response = (
            client.table(CHAT_HISTORY_TABLE)
            .select("session_id,user_message,assistant_message,created_at")
            .order("created_at")
            .execute()
        )
        sessions_dict: dict[str, list[dict]] = {}
        for row in (response.data or []):
            sid = row.get("session_id")
            if not sid:
                continue
            if sid not in sessions_dict:
                sessions_dict[sid] = []
            sessions_dict[sid].append(row)

        summary_list = []
        for sid, turns in sessions_dict.items():
            first_user_msg = turns[0].get("user_message", "")
            title = first_user_msg[:45].strip() if first_user_msg else "New Chat"
            last_created = turns[-1].get("created_at") or turns[0].get("created_at")

            formatted_msgs = []
            for i, t in enumerate(turns):
                u_text = t.get("user_message", "")
                a_text = t.get("assistant_message", "")
                t_stamp = t.get("created_at", "")
                if u_text:
                    formatted_msgs.append({
                        "id": f"{sid}-u-{i}",
                        "role": "user",
                        "content": u_text,
                        "timestamp": t_stamp,
                    })
                if a_text:
                    formatted_msgs.append({
                        "id": f"{sid}-a-{i}",
                        "role": "assistant",
                        "content": a_text,
                        "timestamp": t_stamp,
                    })

            summary_list.append({
                "id": sid,
                "title": title,
                "messages": formatted_msgs,
                "created_at": last_created,
            })

        # Sort newest session first
        summary_list.sort(key=lambda s: s.get("created_at") or "", reverse=True)
        return summary_list
    except Exception as e:
        logger.warning("Failed to fetch sessions summary from chat_history: %s", e)
        return []


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

