from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List
from repositories.client import _get_client

logger = logging.getLogger(__name__)
CHAT_HISTORY_TABLE = "chat_history"


@dataclass
class ChatMessage:
    role: str
    content: str


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
