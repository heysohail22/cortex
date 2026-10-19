# Jev evidence assessment and correction

Phase 2 replaces the Groq retrieval classifier with Jev. Query rewriting remains a separate, conditional call to the existing fast Groq model. No database schema or embedding migration is required.

## Flow

1. Retrieve within the existing session scope. Preserve database failures as errors, not empty results.
2. Merge retained and new evidence, deduplicate it and apply candidate/text budgets.
3. Submit one Jev batch containing passage role and injection questions plus combined safe-evidence sufficiency.
4. SUFFICIENT generates immediately. PARTIAL or NONE can enter one targeted correction; UNKNOWN returns a temporary response.
5. The rewriter can request clarification or supply a query targeting missing requirements. Empty, equivalent or failed rewrites skip duplicate retrieval.
6. Reassess the retained/new union once. Generate a supported partial answer, return a deterministic no-evidence response, or use explicitly permitted public supplementation.

`retrieval_corrections_used` starts at zero and increments only when scheduling correction retrieval. It never exceeds one. `db_retry_count` is maintained as a compatibility mirror. Initial retrieval is not a correction. A single retrieval-stage deadline bounds retrieval, assessment, rewriting and any optional public supplementation; each operation also has its own timeout.

## Decisions and safety

The typed assessment returns SUFFICIENT, PARTIAL, NONE or UNKNOWN. Legacy API labels remain CORRECT, AMBIGUOUS, INCORRECT and UNKNOWN respectively. New optional response fields expose evidence_status, retrieval_status and retrieval_corrections_used. Detailed assessment timing, usage and per-passage decisions are retained in graph results.

Each passage has a locally assigned stable evidence ID. Jev returns a fixed role choice for each supplied ID, so it cannot invent a selected reference. Missing/extra questions, unexpected choices and invalid scores become UNKNOWN. Contradictory useful evidence is retained and conservatively classified as partial; uncertain or malicious instruction passages are excluded. Removing useful unsafe passages cannot leave a sufficient verdict unchanged.

Empty successful retrieval can become NONE without a Jev request. Database and provider errors cannot. NONE describes the retrieved subset, not proof that the entire corpus has no answer.

Only assessed text reaches generation: truncated tails are not restored afterward. Budgets reserve formatting room for document and hybrid generation. Useful retained chunks keep their identity after truncation, preventing duplicate insertion on correction.

## Configuration

The existing TYPESAFE_API_KEY and JEV_MODEL settings are reused. New settings in .env.example:

- TIMEOUT_RETRIEVAL_STAGE: total stage budget, default 25 seconds.
- TIMEOUT_RETRIEVAL_REWRITE: per-rewrite limit, default 4 seconds.
- MAX_EVIDENCE_CONTEXT_CHARS: candidate context ceiling, default 8000 characters, further limited by generation budgets.
- MAX_EVIDENCE_PASSAGE_CHARS: per-passage ceiling, default 2000 characters.
- MAX_EVIDENCE_CANDIDATES: candidate count ceiling, default 10.
- JEV_EVIDENCE_INJECTION_MAX: exclude at or above this score, default 0.35. This is an initial policy value requiring calibration.

SDK retry settings remain bounded by the outer operation timeout.

## Public supplementation

Document-only is the default. There is no automatic web fallback for weak document retrieval.

Trusted server callers can pass external_evidence_policy="public_supplement" and an independently approved approved_public_query to run_crag_async. The public chat request does not accept these fields. The caller must approve a query without private identifiers or private document facts; the application cannot determine every confidential identifier automatically. The query is additionally redacted before search. Neither private passages nor conversation history are used to construct the external query.

At most one public search runs. Its snippets are assessed before use and excluded snippets are not passed to generation. Public results cannot establish missing private policy facts. Hybrid generation receives distinct document and web context. Web failure falls back to retained partial evidence or a limitation response. Assessment failures and exhausted stage deadlines return temporary unavailable responses.

The existing document-only groundedness judge does not verify supplemented web/hybrid answers. Those are explicitly NOT_CHECKED and is_grounded=false, without a repair loop pretending to verify them. The broader verification redesign remains a separate phase.

## Validation and limits

Run `.venv/bin/python -m pytest tests/ -q` from backend. The phase adds provider-contract, graph-bound, partial-evidence retention, deadline, public-policy and API-output regression tests using mocks.

Live Jev quality, model availability, token cost and latency require configured credentials and a labelled comparison dataset. Mock tests establish orchestration behavior, not detection accuracy or a speed improvement. Supabase retrieval still uses the existing scoped RPC; no authorization model was added or changed.
