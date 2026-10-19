# Cortex rebuild plan and Jev router integration

Status: planned. No backend implementation changes yet.

Rebuild Cortex incrementally, beginning with replacing the Groq intent classifier with Jev. Preserve the working application and existing protections during migration. Rewrite the broader guardrails and evaluation framework after the core graph is working. This is an implementation plan; the changes have not yet been applied.

# Rebuild sequence

1. Replace the router with a Jev adapter and separate direct answer generation from routing.

2. Replace retrieval assessment with Jev, preserving useful evidence and allowing one targeted retrieval correction.

3. Standardize generation for document, web, hybrid and direct answers. Compare generator models before changing the default.

4. Verify evidence based answers, allow one repair, and represent failed checks as unverified.

5. Rewrite guardrails and the evaluation framework around the final graph. Preserve focused regression tests throughout the rebuild.

# Router responsibilities

Use one Jev request with separate structured questions for intent, attempted prompt injection or jailbreak, and harmful request assessment. Intent choices are rag, web_search and direct_answer. Keep safety decisions separate from intent so mentioning a sensitive topic does not automatically become a refusal. Python applies the safety policy before executing the selected route. Jev assessment quality must be validated; combining questions does not guarantee protection.

# Inputs and outputs

Inputs: redacted user question, bounded relevant conversation context, current date, document availability and compact document profiles. Document metadata and conversation text are untrusted context, not instructions.

Outputs: intent, separate safety assessments, confidence or probabilities as provided by the API, provider/model identity, decision status and elapsed time. Do not fabricate confidence values or treat a timeout as safe. Disable document routing when no accessible documents exist. Route selection must honor document ownership and access checks.

# Implementation steps

1. Inspect the current SDK documentation and verify model availability with the configured account.

2. Add the supported Python SDK and update pyproject.toml, uv.lock and the requirements mirror together.

3. Add server side TYPESAFE_API_KEY, a configurable Jev model, request timeout and bounded retry settings. Add placeholders to .env.example; never commit secrets.

4. Add a reusable asynchronous Jev client in a dedicated service adapter. Keep provider details out of graph nodes.

5. Replace classify_async internals while preserving its public contract during migration. Keep a feature flag for rollback.

6. Separate the router decision node from direct answer generation. Apply safety policy before any downstream search or generation, including explicit web search overrides.

7. Define an explicit unknown/error path. If safety assessment is unavailable, return a controlled temporary response rather than silently proceeding as safe. For uncertain intent, prefer accessible document retrieval when relevant or ask for clarification.

8. Record decision latency, errors and usage without logging raw secrets or sensitive messages.

# Rate limiting

Keep rate limiting before all external model and search calls. It is an inexpensive application check that limits abuse, accidental loops and unexpected API spending; it does not require a model.

Preserve separate chat and upload limits. Return HTTP 429 with Retry After information. Set limits from expected traffic and provider quotas rather than arbitrary promises. Add a bound on concurrent expensive requests to prevent overload.

Use authenticated user identity when available, with a carefully derived client IP fallback for anonymous use. A client supplied session ID alone is not a trustworthy quota identity. Trust proxy headers only from configured proxies.

The existing in memory limiter is suitable for a single process interview demo. Multiple workers or instances require a shared limiter or gateway because process local counters do not enforce one global limit.

# Acceptance checks

- Document, live information and direct questions choose the expected route.

- No document access means no RAG route.

- Safety decisions override intent and explicit search commands.

- Harmless educational questions are not blocked merely for mentioning attacks.

- Timeout, rate limit and malformed provider responses take a controlled error path.

- Direct generation occurs outside the router and output checks still apply.

- Existing API contracts and focused reliability tests pass.

- Compare routing accuracy, false safety blocks, missed attacks, median and p95 latency, and total request cost against the current router. Do not claim a speedup until measured.

# Later documents

Create follow up plans for retrieval correction, answer generation and verification, then the guardrail rewrite and evaluation dataset. The retrieval plan must prevent automatic public web substitution for missing internal facts. The verification plan must distinguish evidence support from absolute truth.

# References

[TypeSafe structured questions](https://docs.typesafe.ai/primitives.md)

[TypeSafe Python SDK](https://docs.typesafe.ai/sdk/python.md)

[TypeSafe guardrail example](https://docs.typesafe.ai/cookbooks/llm_guardrails)

Repository starting points: backend/services/router_service.py, backend/crag/nodes.py, backend/crag/edges.py, backend/crag/graph.py, backend/api/chat.py, backend/config.py and backend/guardrails/rate_limiter.py.
