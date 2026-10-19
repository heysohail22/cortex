"""Optional async Gemini generation adapter; no automatic provider fallback."""
from __future__ import annotations

import json

from google import genai
from google.genai import types

import config
from providers.structured import InvalidProviderOutput, StructuredResponse

_client = None


def get_answer_client():
    global _client
    if _client is None:
        if not config.GEMINI_API_KEY:
            raise ValueError("Gemini credentials unavailable")
        _client = genai.Client(api_key=config.GEMINI_API_KEY, http_options=types.HttpOptions(
            retry_options=types.HttpRetryOptions(attempts=config.ANSWER_PROVIDER_RETRIES + 1)))
    return _client.aio


async def close_answer_client() -> None:
    global _client
    if _client is not None:
        await _client.aio.aclose()
        _client.close()
        _client = None


async def generate_structured(*, model: str, system: str, payload: dict, schema: dict,
                              temperature: float, max_tokens: int, timeout: float,
                              reasoning: str | None = None):
    thinking = types.ThinkingConfig(thinking_level=reasoning) if reasoning else None
    response = await get_answer_client().models.generate_content(
        model=model, contents=json.dumps(payload, ensure_ascii=False),
        config=types.GenerateContentConfig(
            system_instruction=system, temperature=temperature, max_output_tokens=max_tokens,
            response_mime_type="application/json", response_json_schema=schema,
            thinking_config=thinking, http_options=types.HttpOptions(timeout=max(1, int(timeout * 1000))),
        ),
    )
    try:
        if not response.candidates or response.candidates[0].finish_reason != types.FinishReason.STOP:
            raise ValueError("Incomplete response")
        data = json.loads(response.text or "")
        if not isinstance(data, dict):
            raise ValueError("Expected object")
    except (ValueError, TypeError) as exc:
        raise InvalidProviderOutput("Invalid structured response", model=getattr(response, "model_version", None) or model,
                                    usage=response.usage_metadata.model_dump(mode="json") if getattr(response, "usage_metadata", None) else None) from exc
    return StructuredResponse(data=data, model=response.model_version or model,
                              usage=response.usage_metadata.model_dump(mode="json") if response.usage_metadata else None)
