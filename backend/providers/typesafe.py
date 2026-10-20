from __future__ import annotations

import math
import httpx2
from typing import Any
from typesafe_sdk import AsyncTypeSafeClient, Choice, Noul, RetryPolicy
import config

_client: AsyncTypeSafeClient | None = None


def get_client() -> AsyncTypeSafeClient:
    global _client
    if _client is None:
        if not config.TYPESAFE_API_KEY:
            raise ValueError("Jev credentials unavailable")
        _client = AsyncTypeSafeClient(
            api_key=config.TYPESAFE_API_KEY, model=config.JEV_MODEL,
            timeout=httpx2.Timeout(None),
            retry=RetryPolicy(max_retries=config.JEV_MAX_RETRIES, timeout=None),
        )
    return _client


async def close_client() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


def _probability(value: Any) -> float:
    number = float(value)
    if not math.isfinite(number) or not 0 <= number <= 1:
        raise ValueError("Invalid assessment")
    return number


def choice_question(*, instructions: str, criteria: dict):
    return Choice(instructions=instructions, criteria=criteria)


def yes_no_question(*, instructions: str):
    return Noul(instructions=instructions)


async def evaluate_questions(*, state: dict, questions: dict):
    return await get_client().system_one(
        state=state, questions=questions, model=config.JEV_MODEL,
    )
