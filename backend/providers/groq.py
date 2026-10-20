from __future__ import annotations

from langchain_groq import ChatGroq
import config


def get_model(model: str, temperature: float) -> ChatGroq:
    """Construct an SDK model; consuming services retain their existing singleton lifecycle."""
    return ChatGroq(model=model, api_key=config.GROQ_API_KEY, temperature=temperature)


_answer_client = None


def get_answer_client():
    global _answer_client
    if _answer_client is None:
        from groq import AsyncGroq
        if not config.GROQ_API_KEY:
            raise ValueError("Groq credentials unavailable")
        _answer_client = AsyncGroq(api_key=config.GROQ_API_KEY, max_retries=config.ANSWER_PROVIDER_RETRIES)
    return _answer_client


async def close_answer_client() -> None:
    global _answer_client
    if _answer_client is not None:
        await _answer_client.close()
        _answer_client = None


async def generate_structured(*, model: str, system: str, payload: dict, schema: dict,
                              temperature: float, max_tokens: int, timeout: float,
                              reasoning: str | None = None):
    import json
    from providers.structured import StructuredResponse, InvalidProviderOutput
    # GPT-OSS reasoning shares the completion budget with the required JSON.
    effective_reasoning = reasoning or ("low" if model.startswith("openai/gpt-oss-") else None)
    options = {"reasoning_effort": effective_reasoning} if effective_reasoning else {}
    try:
        result = await get_answer_client().chat.completions.create(
            model=model, messages=[{"role": "system", "content": system},
                                   {"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
            response_format={"type": "json_schema", "json_schema": {
                "name": "cortex_response", "strict": True, "schema": schema}},
            temperature=temperature, max_completion_tokens=max_tokens, timeout=timeout, **options,
        )
    except Exception as exc:
        # Groq can reject generated JSON before returning a completion. Treat only
        # this documented output failure as repairable; auth/quota errors stay errors.
        body = getattr(exc, "body", None)
        error = body.get("error", body) if isinstance(body, dict) else {}
        if (getattr(exc, "status_code", None) == 400
                and isinstance(error, dict) and error.get("code") == "json_validate_failed"):
            raise InvalidProviderOutput("Provider rejected structured output", model=model) from exc
        raise
    try:
        if not result.choices or result.choices[0].finish_reason != "stop":
            raise ValueError("Incomplete response")
        data = json.loads(result.choices[0].message.content or "")
        if not isinstance(data, dict):
            raise ValueError("Expected object")
    except (ValueError, TypeError) as exc:
        raise InvalidProviderOutput("Invalid structured response", model=result.model,
                                    usage=result.usage.model_dump(mode="json") if result.usage else None) from exc
    return StructuredResponse(data=data, model=result.model, usage=result.usage.model_dump(mode="json") if result.usage else None)
