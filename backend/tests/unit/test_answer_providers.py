from __future__ import annotations

from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, Mock, patch

import pytest

from providers import groq, gemini
from providers.structured import InvalidProviderOutput
from services.answer_contracts import GenerationPayload

ARGS = dict(model="test-model", system="System", payload={"question": "q"}, schema=GenerationPayload.model_json_schema(),
            temperature=0.2, max_tokens=100, timeout=1, reasoning=None)


async def test_groq_structured_request_settings_and_usage():
    create = AsyncMock(return_value=NS(choices=[NS(finish_reason="stop", message=NS(content='{"answer":"Hello","claims":[]}'))],
                                      model="actual-model", usage=NS(model_dump=lambda **kw: {"prompt_tokens": 10})))
    with patch.object(groq, "get_answer_client", return_value=NS(chat=NS(completions=NS(create=create)))):
        response = await groq.generate_structured(**ARGS)
    assert response.model == "actual-model" and response.usage == {"prompt_tokens": 10}
    assert create.call_args.kwargs["response_format"]["json_schema"]["strict"] is True
    assert create.call_args.kwargs["max_completion_tokens"] == 100
    assert "reasoning_effort" not in create.call_args.kwargs


@pytest.mark.parametrize("finish,content", [("length", '{}'), ("stop", 'not-json'), ("stop", '[]')])
async def test_groq_rejects_truncated_and_malformed_responses(finish, content):
    client = NS(chat=NS(completions=NS(create=AsyncMock(return_value=NS(choices=[NS(finish_reason=finish, message=NS(content=content))], model="m", usage=None)))))
    with patch.object(groq, "get_answer_client", return_value=client):
        with pytest.raises(InvalidProviderOutput):
            await groq.generate_structured(**ARGS)


async def test_gemini_structured_request_and_usage():
    create = AsyncMock(return_value=NS(candidates=[NS(finish_reason="STOP")], text='{"answer":"Hello","claims":[]}',
                                      model_version="pinned-version", usage_metadata=NS(model_dump=lambda **kw: {"prompt_token_count": 10})))
    with patch.object(gemini, "get_answer_client", return_value=NS(models=NS(generate_content=create))):
        response = await gemini.generate_structured(**ARGS)
    assert response.model == "pinned-version"
    cfg = create.call_args.kwargs["config"]
    assert cfg.max_output_tokens == 100 and cfg.response_mime_type == "application/json"
    assert cfg.http_options.timeout == 1000
    assert cfg.system_instruction == "System"


async def test_gemini_rejects_truncated_output():
    with patch.object(gemini, "get_answer_client", return_value=NS(models=NS(generate_content=AsyncMock(return_value=NS(candidates=[NS(finish_reason="MAX_TOKENS")]))))):
        with pytest.raises(InvalidProviderOutput):
            await gemini.generate_structured(**ARGS)


def test_provider_clients_disable_hidden_retries():
    with patch.object(groq, "_answer_client", None), patch("config.GROQ_API_KEY", "dummy"), patch("config.ANSWER_PROVIDER_RETRIES", 0), patch("groq.AsyncGroq") as constructor:
        groq.get_answer_client()
        assert constructor.call_args.kwargs["max_retries"] == 0
    with patch.object(gemini, "_client", None), patch("config.GEMINI_API_KEY", "dummy"), patch("config.ANSWER_PROVIDER_RETRIES", 0), patch("providers.gemini.genai.Client") as constructor:
        gemini.get_answer_client()
        assert constructor.call_args.kwargs["http_options"].retry_options.attempts == 1
