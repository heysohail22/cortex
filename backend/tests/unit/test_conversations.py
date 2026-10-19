from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from repositories.conversations import ChatMessage, get_messages
from services.conversations import get_native_conversation_turns


def test_repository_preserves_session_filter_and_turn_order():
    client = Mock()
    client.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = SimpleNamespace(
        data=[{"user_message": "Question", "assistant_message": "Answer"}]
    )
    with patch("repositories.conversations._get_client", return_value=client):
        messages = get_messages("my-session")
    client.table.assert_called_once_with("chat_history")
    client.table.return_value.select.return_value.eq.assert_called_once_with("session_id", "my-session")
    assert messages == [ChatMessage("user", "Question"), ChatMessage("assistant", "Answer")]


async def test_budgeting_uses_repository_messages_and_summarizes_only_older_turns():
    messages = [ChatMessage("user", "old question"), ChatMessage("assistant", "old answer"), ChatMessage("user", "latest question")]
    with patch("services.conversations.get_messages", return_value=messages), \
         patch("config.MAX_CONVERSATION_TOKENS", 1), patch("config.MAX_RECENT_MESSAGES", 1), \
         patch("services.conversations._summarize_messages", AsyncMock(return_value="Earlier context")) as summarize:
        result = await get_native_conversation_turns("my-session")
    summarize.assert_awaited_once_with(messages[:-1])
    assert result[0].type == "system" and "Earlier context" in result[0].content
    assert result[1].type == "human" and result[1].content == "latest question"
