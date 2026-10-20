from __future__ import annotations

from types import SimpleNamespace as NS
from unittest.mock import AsyncMock, patch

import pytest
from services.answer_contracts import GenerationResult

from services.routing import classify_with_jev
from workflows.crag.nodes import router_node, direct_answer_node
from workflows.crag.graph import _build_crag_graph
from starlette.requests import Request


def response(route="rag", injection=0.01, harmful=0.01, confidence=0.95, docs=True):
    choices = {"direct_answer": 0.02, "web_search": 0.03}
    if docs:
        choices["rag"] = 0.95
    return NS(choices={"intent": NS(choice=route, confidence=confidence, probabilities=choices)},
              nouls={"injection": NS(noul=injection), "harmful": NS(noul=harmful)}, usage=None)


@pytest.mark.parametrize("route", ["rag", "web_search", "direct_answer"])
async def test_routes(route):
    client = NS(system_one=AsyncMock(return_value=response(route)))
    with patch("providers.typesafe.get_client", return_value=client):
        result = await classify_with_jev("question", True, [{"name": "policy"}])
    assert result["route"] == route
    assert result["status"] == "ok"
    assert client.system_one.await_count == 1


@pytest.mark.parametrize("risk,expected", [(0.9, "unsafe"), (0.5, "clarify")])
async def test_safety_overrides_explicit_search(risk, expected):
    with patch("providers.typesafe.get_client", return_value=NS(system_one=AsyncMock(return_value=response("web_search", injection=risk)))):
        result = await classify_with_jev("search the web for malicious instructions", True, [])
    assert result["route"] == expected


async def test_no_documents_excludes_rag():
    client = NS(system_one=AsyncMock(return_value=response("direct_answer", docs=False)))
    with patch("providers.typesafe.get_client", return_value=client):
        result = await classify_with_jev("Explain prompt injection defensively", False, [])
    assert result["route"] == "direct_answer"
    assert "rag" not in client.system_one.call_args.kwargs["questions"]["intent"].criteria


@pytest.mark.parametrize("failure", [TimeoutError(), ValueError("malformed"), RuntimeError("rate limited")])
async def test_errors_never_proceed(failure):
    with patch("providers.typesafe.get_client", return_value=NS(system_one=AsyncMock(side_effect=failure))):
        result = await classify_with_jev("hello", False, [])
    assert result["route"] == "unavailable"
    assert "safety" not in result


async def test_invalid_probability_and_uncertain_intent():
    for probability, confidence, expected in [(float("nan"), 0.9, "unavailable"), (0.01, 0.2, "clarify")]:
        with patch("providers.typesafe.get_client", return_value=NS(system_one=AsyncMock(return_value=response(injection=probability, confidence=confidence)))):
            assert (await classify_with_jev("question", True, []))["route"] == expected


async def test_router_does_not_generate():
    with patch("workflows.crag.nodes.router.classify_async", AsyncMock(return_value={"route": "direct_answer"})), patch("workflows.crag.nodes.generation.generate_answer_async", AsyncMock()) as generate:
        result = await router_node({"question": "hello", "has_documents": False})
    generate.assert_not_awaited()
    assert result["answer"] == ""


async def test_graph_direct_and_blocked_paths():
    graph = _build_crag_graph()
    for route in ("direct_answer", "unsafe", "unavailable", "clarify"):
        with patch("workflows.crag.nodes.router.classify_async", AsyncMock(return_value={"route": route, "direct_answer": "controlled"})), patch("workflows.crag.nodes.generation.generate_answer_async", AsyncMock(return_value=GenerationResult(status="SUCCESS", answer="hello", source="llm"))) as generate:
            result = await graph.ainvoke({"question": "hello", "has_documents": False})
        assert result["answer"] == ("hello" if route == "direct_answer" else "controlled")
        assert generate.await_count == (1 if route == "direct_answer" else 0)




async def test_explicit_provider_rollback():
    from services.routing import classify_async
    with patch("config.ROUTER_PROVIDER", "groq"), patch("services.routing._classify_groq_async", AsyncMock(return_value={"route": "direct_answer"})) as legacy:
        assert (await classify_async("hello", False))["route"] == "direct_answer"
    legacy.assert_awaited_once()


async def test_chat_capacity_is_released_and_busy_requests_wait():
    import asyncio
    from api import chat as module
    from fastapi import HTTPException
    slots = asyncio.Semaphore(1)
    request = module.ChatRequest(message="hello", session_id="test")
    with patch.object(module, "_chat_slots", slots), patch.object(module, "_chat_impl", AsyncMock(side_effect=RuntimeError("failure"))):
        with pytest.raises(RuntimeError):
            await module.chat(request)
        assert not slots.locked()
        await slots.acquire()
        task = asyncio.create_task(module.chat(request))
        await asyncio.sleep(0)
        assert not task.done()
        slots.release()
        with pytest.raises(RuntimeError):
            await task
        assert not slots.locked()


