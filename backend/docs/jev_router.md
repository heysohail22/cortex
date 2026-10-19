# Jev router integration

The first rebuild phase replaces intent classification with one TypeSafe request containing intent, injection and harmful-request questions. Retrieval evaluation, generation and groundedness services remain unchanged.

## Configure

Run `uv sync` in `backend`. Add `TYPESAFE_API_KEY` to `backend/.env`. The router defaults to `ROUTER_PROVIDER=jev`, `JEV_MODEL=jev`, a five second overall deadline and no SDK retries. Use `ROUTER_PROVIDER=groq` for explicit rollback to the legacy classifier. This rollback does not provide Jev's separate safety assessments; existing local protections remain enabled.

The Jev alias may change upstream. Before a live rollout, use `AsyncTypeSafeClient.models.list()` with your account, select an available model, and pin its ID in `JEV_MODEL` for reproducible comparisons. Missing credentials or a failed safety assessment produces a temporary controlled response, never a safe verdict.

The initial review, blocking and intent thresholds in `.env.example` are starting policy values, not calibrated guarantees. Review-range safety scores and low confidence intent return clarification without running tools. Educational discussion is explicitly distinguished from attack instructions.

## Graph and telemetry

Routing and direct generation are separate nodes. Unsafe, uncertain and unavailable decisions terminate before downstream generation or search. Explicit web requests pass through the same safety assessment. All answers still pass API output checks.

Graph state and `run_crag_async` results include `router_decision` with provider, model, status, elapsed milliseconds, and successful assessments and usage. No confidence or safety values are invented on error. The public chat response remains backward compatible. Logs contain status, timing and exception class, not provider exception payloads or submitted text.

A reusable async client is closed on FastAPI shutdown. Input context uses bounded document profiles and recent conversation text, with document routing disabled if no accessible documents exist. This does not add authentication or replace the repository's existing access-control assumptions.

## Rate limiting and overload

Existing chat and upload rate limits remain before external work. Identity uses the ASGI peer rather than caller supplied session IDs or forwarding headers. Configure Uvicorn's trusted proxy settings for your actual deployment; never trust arbitrary forwarders. The application has no authenticated principal today.

`MAX_CONCURRENT_CHATS` bounds active chat work per process; overload receives HTTP 503 and Retry-After. Rate-limit responses remain HTTP 429 with Retry-After. Multiple workers need shared counters and concurrency coordination before these limits can be treated as deployment-wide.

## Validation

Run `.venv/bin/python -m pytest tests/ -q` from `backend`. Router tests use mocked provider responses and cover route choices, safety precedence, uncertainty, malformed responses, provider errors, no-document routing, and graph termination. These tests validate integration behavior, not real model safety accuracy.

Before claiming a speed or quality improvement, compare the existing and Jev routers on the same labelled questions. Record routing accuracy, false blocks, missed attacks, median and p95 latency, retries, token usage and cost per completed answer. Real account access and live evaluation are required.

## Deferred phases

Retrieval correction and typed generation/verification are now implemented as subsequent phases. See [retrieval](jev_retrieval.md) and [generation and verification](generation_verification.md). Live model selection and the broader guardrail/evaluation rewrite remain separate work.
