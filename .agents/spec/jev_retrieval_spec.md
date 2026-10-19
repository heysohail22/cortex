# Cortex Jev retrieval assessment and correction specification

Status: planned. Phase 2 follows [Jev router integration](jev_router_spec.md). This specification authorizes no claim of measured speed, cost or accuracy improvement. It describes the next implementation; no application code changes are included in this document task.

## Objective

After fetching chunks from the vector database, use Jev to select useful evidence and assess whether the combined context answers the original question. Generate immediately when sufficient. For partial or absent evidence, allow at most one targeted rewrite and retrieval correction. Preserve supported information, stop bounded retries, and never substitute public facts for missing private document facts.

## Scope

Replace the retrieval assessment portion of the current Groq evaluator. Separate assessment from text-generating query rewriting. Update graph state, routing, service contracts and focused regression tests. Preserve the implemented Jev router, rate limiting, document access boundaries, existing input protections and output checks.

Generation model selection, the general guardrail rewrite and the full evaluation framework rewrite remain later phases. Add only the generation inputs and controlled response paths required to represent partial or missing evidence correctly. Existing post-generation verification remains a separate check of answer faithfulness.

## Current behavior to replace

- `services/evaluator_service.py` combines retrieval decisions and query rewriting in a reasoning-model call.
- `retrieval_eval_node` and its service can treat assessment errors as CORRECT.
- AMBIGUOUS evidence goes directly to web augmentation.
- Exhausted INCORRECT evidence goes automatically to web search.
- Retry counters are incremented during evaluation rather than recording completed correction attempts consistently.
- Empty results and retrieval failures can both appear as empty evidence.

The new implementation must not interpret a provider failure as successful assessment or proof that documents lack an answer.

## Evidence assessment contract

Use explicit internal statuses:

| Status | Meaning |
| --- | --- |
| SUFFICIENT | The selected passages jointly support an answer to all material parts of the question. |
| PARTIAL | At least one useful fact is supported, but a material part is missing or unresolved. |
| NONE | The retrieved set contains no usable answer evidence. This is not proof that the whole corpus lacks the answer. |
| UNKNOWN | The assessment failed, timed out or returned an invalid response. |

For API compatibility, map SUFFICIENT to CORRECT, PARTIAL to AMBIGUOUS and NONE to INCORRECT in the existing `evaluation_result` field. Expose UNKNOWN explicitly; do not force it into a successful legacy label. The graph should route from the new typed assessment status.

Jev supplies bounded choices and scores. Python validates the response and makes the routing decision. Jev does not generate rewritten search queries or explanations.

Inputs:

- Original user question and bounded context needed to resolve references.
- Candidate passages with stable IDs, source metadata and text.
- Document scope and an explicit external evidence policy.
- Any previously retained evidence and original question requirements on a retry.

Outputs:

- Selected evidence IDs validated against supplied candidates.
- Combined evidence status.
- Per-passage relevance, usable evidence and injection assessments where requested.
- Conflicting passage IDs or a conflict indicator. Preserve substantive contradictions; do not silently label one side true.
- Provider, model, decision status, elapsed time and available usage.

Retain provider-returned confidence or scores where applicable. Do not invent them for errors. Derive user-visible explanations from application templates or the generation step, not fabricated Jev reasoning text.

## Request design and evidence handling

Start with the existing small top-k candidate set. Prefer one bounded request containing questions about the set and candidate IDs rather than serial API requests per passage. Assess combined sufficiency explicitly: several individually incomplete passages can jointly answer a question.

If SDK or model limits require separate candidate assessments, use bounded concurrency and one set-level sufficiency decision; measure the added requests and latency. Do not assume separate relevance scores can be combined into proof of answer coverage.

Treat all retrieved text as untrusted data. Exclude passages classified as malicious instructions according to configured policy. An uncertain injection assessment must not silently pass as safe. This semantic assessment complements existing ingestion protections; it does not establish immunity to injection.

Preserve provenance and access scope. Deduplicate by persistent chunk ID where available, otherwise by document identity and normalized text hash. Keep useful first-pass evidence across correction. Reassess the bounded union of retained and new evidence, without discarding useful facts merely because they were absent from the second search.

Apply context budgets before sending model requests. If truncation omits potentially useful content, do not claim the original full context was assessed. Tune top-k and budgets with examples rather than increasing them without limits.

## Graph flow

```text
Vector retrieval
      |
      v
Jev evidence assessment
      |
      +-- SUFFICIENT --> Generate supported answer --> Existing verification
      |
      +-- PARTIAL / NONE, no correction used
      |        |
      |        v
      |   Clarify if ambiguous; otherwise targeted query rewrite
      |        |
      |        v
      |   One retrieval correction --> Merge and deduplicate --> Reassess
      |
      +-- PARTIAL / NONE, correction exhausted
      |        |
      |        v
      |   Supported partial answer / no evidence response /
      |   clarification / explicitly permitted external evidence
      |
      +-- UNKNOWN --> Controlled temporary response
```

Retrieval infrastructure failure also takes a controlled temporary response rather than masquerading as NONE. A failed retrieval or assessment does not consume a successful assessment verdict. Request deadlines still bound all work.

## Query rewriting policy

Do not rewrite successful questions. Rewriting adds an LLM call and is justified only when the first result is partial or unhelpful and a clearer query could improve retrieval.

For PARTIAL, target missing requirements while retaining useful evidence. For NONE, express the same intent with clearer entities and terminology. Preserve names, dates, scope and constraints; never introduce assumed facts.

Use the existing fast generation provider for rewriting initially. Pass the original question, bounded retained evidence and evidence status so the rewriter can identify the missing part. A structured rewrite response may describe the missing requirement and a clarification need; validate and bound these fields. Do not add an extra model call solely to narrate Jev's verdict.

If the question is ambiguous and history does not resolve it, ask one focused clarification instead of guessing. If the proposed rewrite is empty, equivalent to the original, fails or times out, skip duplicate retrieval and finalize from the assessed evidence. A failed rewrite is not a reason to start an unbounded correction loop.

Example: the question asks for refund deadline and fee. The first passages support the deadline. Preserve them and search for refund fees or deductions; do not discard the deadline evidence.

## Retry semantics

Use `retrieval_corrections_used`, initially 0, incremented when scheduling the single correction retrieval. Maximum value is 1. Initial retrieval does not count as a correction. PARTIAL and NONE share the same budget; switching labels never resets it.

Maximum normal path: two vector retrieval attempts and two evidence assessments. The correction path adds at most one query rewrite. Empty successful retrieval results can be labelled NONE deterministically without paying for Jev. Do not skip assessment of retained useful evidence if a correction returns no new candidates.

Enforce per-operation timeouts and an overall retrieval-stage deadline. SDK retries must fit within that deadline. On exhausted time, terminate with a controlled outcome; do not launch additional fallback chains.

## Behavior after correction

| Final state | Required behavior |
| --- | --- |
| SUFFICIENT | Generate using selected evidence with citations. |
| PARTIAL | Answer supported portions with citations and state precisely what could not be found. |
| NONE for document-specific facts | Explain that the available retrieval found no supporting evidence; request the relevant document or clarification where useful. |
| Ambiguous question | Ask a focused question. |
| External information appropriate and explicitly permitted | Search once for public evidence; attribute it separately and disclose remaining document gaps. |
| UNKNOWN or retrieval infrastructure failure | Return a temporary unavailable response, not a no-evidence claim. |

For NONE, a deterministic response avoids an unnecessary generation call. For PARTIAL, generation must receive the evidence status and missing requirements, and must not fill gaps using model memory.

For example: "The policy gives a 30-day refund deadline. I could not find the applicable fee in the retrieved policy passages."

## Web fallback policy

Default to document-only when the request is scoped to uploaded documents or private/internal facts. No automatic web fallback merely because evidence is weak.

External supplementation must be allowed by explicit user intent, a trusted request setting or established application policy. A model score alone cannot grant permission to disclose private details to a search provider. Queries sent externally must omit private document text, secrets and private identifiers.

Public information may supplement an externally answerable question; it must not be presented as the company's own policy. Search failure or insufficient public evidence ends in a partial answer or transparent limitation, never a fallback to invented facts. Existing web answer verification limitations are a separate follow-up and must not be labelled as successful verification.

## Proposed implementation locations

- `backend/services/jev_service.py`: reuse shared client lifecycle, timeouts and safe telemetry; expose a retrieval assessment adapter without coupling it to the router function.
- `backend/services/evaluator_service.py`: typed evidence assessment and validated provider response mapping.
- `backend/services/search_service.py`: targeted rewrite accepting retained evidence and original requirements.
- `backend/crag/state.py`: evidence status, retained evidence, assessment metadata, retrieval status, correction count, external evidence policy and missing requirements.
- `backend/crag/nodes.py`: assessment, correction, explicit partial/no-evidence/unavailable paths and evidence merging.
- `backend/crag/edges.py`: deterministic routing with one shared correction bound.
- `backend/crag/graph.py`: register correction and terminal paths without restarting the entry router.
- `backend/services/generator_service.py`: minimal support for partial evidence instructions and provenance.
- `backend/api/chat.py`: preserve existing response fields and add optional assessment metadata only where useful.
- `backend/config.py` and `.env.example`: configurable budgets, deadlines and explicitly documented policy thresholds.

No schema or embedding migration is required by this phase. Keep existing authorization filters on every initial and correction retrieval.

## Acceptance checks

- Sufficient evidence generates without query rewriting or web search.
- Two individually partial passages that jointly cover the question are accepted as sufficient.
- Partial evidence is retained across a targeted correction, including when the correction returns no new chunks.
- NONE triggers at most one useful rewrite and correction.
- Partial-to-none and none-to-partial transitions do not reset the correction budget.
- Empty, unchanged and failed rewrites do not repeat the same retrieval.
- Ambiguous questions ask for clarification without inventing entities.
- Missing private policy facts never trigger automatic public web substitution.
- Permitted public supplementation preserves source attribution and does not send private context externally.
- Unknown IDs, missing assessments, nonfinite scores and provider failures cannot become CORRECT.
- Actual empty results and database errors take different paths.
- Injection-marked passages are excluded; meaningful factual contradictions remain visible.
- Public API compatibility and existing relevant reliability tests pass after updating old fallback expectations.
- No-evidence and terminal responses still pass output checks.

Focused tests mock provider decisions to verify orchestration. Human-labelled examples separately measure whether Jev's decisions are accurate.

## Performance comparison

Use the same questions, candidate passages and access scope for baseline and new assessments. Measure evidence selection quality, answer coverage, downstream groundedness, correction frequency, external search frequency, provider failures, median and p95 latency, and cost per completed answer including retries.

Include sufficient, partial, irrelevant, conflicting, multi-passage and malicious-context examples. Record missed evidence and false rejection of useful passages. Optimize total answer latency and quality rather than only the duration of one Jev call.

## References

- [TypeSafe passage classification](https://docs.typesafe.ai/cookbooks/classifying_rag_passages)
- [TypeSafe structured questions](https://docs.typesafe.ai/primitives.md)
- [TypeSafe Python SDK](https://docs.typesafe.ai/sdk/python.md)
