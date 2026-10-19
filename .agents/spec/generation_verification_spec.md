# Cortex generation and answer verification specification

Phase 3 follows the implemented Jev router and bounded retrieval correction. Standardize answer generation, citations and post-generation verification across document, web, hybrid and direct routes. Optimize measured latency and cost while preserving honest evidence boundaries. Status: planned; this specification does not change application code.

# Decisions and scope

Use one configured generator per request. Keep the existing Groq generator as the migration default and baseline; evaluate Gemini Flash-Lite as a candidate before changing the default. Do not automatically run a small model and then a large model on every request. Keep verification for evidence-based answers and allow at most one answer repair. The broader input guardrail and evaluation-framework rewrites remain separate phases; focused regression tests belong to this implementation.

Generation answers the question using selected evidence. Verification checks whether the answer faithfully reflects that evidence, not whether the source itself is objectively correct. Do not repeat retrieval sufficiency assessment after generation or restart retrieval because of a generation error.

# Current gaps to fix

The generation service currently turns some provider failures into ordinary answer strings. Citation lists are assembled from supplied sources rather than explicit claim support. The verification service and node can mark errors or timeouts as grounded, and some skipped checks report entailment. Public supplementation is currently marked unverified by the document-only judge. Replace these behaviors with explicit generation and verification outcomes. Preserve the implemented router and retrieval retry bounds.

# Generation inputs

Pass the original question, bounded relevant conversation history, the route, evidence status, missing requirements, conflicts and selected evidence. Every passage needs a stable evidence ID, source kind, document identity or web URL, and the exact text supplied to generation. Preserve the selected and sanitized evidence from retrieval; do not restore truncated or excluded text.

Create a generation evidence snapshot after applying the final context budget. The verifier must inspect that same snapshot. If the final budget removes evidence needed for completeness, do not continue advertising a sufficient answer; re-budget without another retrieval loop, or disclose the limitation. Include source dates when available without inventing them. Conversation history resolves references but does not establish document facts.

# Route behavior

| Route or evidence state | Generation behavior |
| --- | --- |
| Document SUFFICIENT | Answer material requirements from the selected document evidence and cite support. |
| Document PARTIAL | Answer supported portions and identify unresolved requirements. Never fill private-fact gaps from model memory. |
| Document NONE or UNKNOWN | Use existing deterministic missing-evidence or unavailable paths; do not invoke a generator to invent an answer. |
| Web | Use selected public evidence; cite claims and preserve available dates and qualifications. |
| Hybrid | Distinguish document evidence from public supplementation. Public sources cannot establish missing private policy facts. |
| Direct | Answer general, coding or creative questions normally. Do not claim source verification or invent citations. |
| Conflicting evidence | Explain the disagreement with support from both sides; do not silently choose a winner. |

# Prompt and output contract

Keep governing instructions in the system message. Treat retrieved documents, web content, gap descriptions and conversation history as untrusted data. Require concise answers, explicit limitations and stable evidence references. Preserve legitimate refusals and clarify unresolved ambiguity without inventing entities.

Use a typed internal GenerationResult with status SUCCESS, ERROR or TIMEOUT; answer text; claim or sentence support references; and provider, model, elapsed time and available usage. Validate that every referenced ID belongs to the generation snapshot and that its source kind matches the claim. Provider errors are operational outcomes, never factual answers. Missing output, malformed structure and invalid references cannot be accepted as successful grounded generation.

Keep public source badges and citation lists backward compatible by mapping validated evidence IDs to document names and URLs. The internal support mapping must remain precise enough for the judge to check individual factual claims. Avoid manual duplicate source footers. Validation of a known ID proves only that the source exists; semantic support requires verification.

# Model configuration and provider boundaries

Keep provider and model selection in server configuration, independent of routing and evidence-assessment models. Add an optional Gemini provider adapter alongside the existing Groq adapter. Confirm current model IDs, SDK APIs, account access and pricing from official documentation during implementation; do not bake an unverified model alias into this spec.

Compare the existing GPT-OSS-120B deployment on Groq with an available Gemini Flash-Lite model using identical questions, evidence snapshots, output-length limits and prompts. Add a regular Gemini Flash candidate only if Flash-Lite fails important cases. DeepSeek and GLM are deferred unless the comparison establishes a need.

Keep temperature, output-token limits, reasoning settings where supported, timeouts and allowed retries explicit. Add a rollback configuration. Never route provider failure to a more expensive model silently. A stronger repair model may be enabled only after measured benefit; it consumes the same single repair allowance.

# Verification contract

Use a typed VerificationResult: SUPPORTED, UNSUPPORTED, UNKNOWN or SKIPPED; bounded unsupported claim references; invalid or unsupported citation references; provider/model identity; elapsed time and actual usage. Preserve real provider scores when available, but never fabricate confidence on failure.

| Verdict | Meaning and action |
| --- | --- |
| SUPPORTED | All material factual claims in the checked answer are supported by the generation snapshot, and citation mappings are valid. Return the answer. |
| UNSUPPORTED | At least one factual claim is contradicted or not justified, a citation misrepresents evidence, or the answer hides a material known gap. Repair once if budget remains. |
| UNKNOWN | The judge failed, timed out, returned malformed output or did not cover the required answer. Do not report successful verification. |
| SKIPPED | Evidence verification does not apply, such as a direct greeting or creative answer. Do not label it grounded or fact-checked. |

Example: the evidence states that annual leave is 20 days. An answer adding that unused leave carries over is unsupported even if the carryover claim happens to be true elsewhere. Retrieval may have been sufficient to answer the leave-days question; verification catches the added claim.

Check document, web and hybrid answers against their supplied evidence. A partial answer is supported if its stated facts are backed and it honestly acknowledges gaps. Report conflicting facts as conflicts rather than forcing a single conclusion. Assessing only sampled claims is not full-answer verification; if limits prevent checking all material claims, use UNKNOWN or an explicit limited-check status rather than SUPPORTED.

Start with a corrected version of the existing independent judge. Make Jev an optional verification backend only after comparing it with human-labelled supported, contradicted and unsupported answers. Reuse the TypeSafe adapter and batch compatible questions if that option is implemented; do not add Jev before an unchanged judge call. A model must not approve its own draft merely through a self-reported grounded flag.

# Graph and repair budget

```text
Selected evidence and original question
                 |
                 v
Generate once and validate structure and references
                 |
                 v
Verify final answer against the generation snapshot
                 |
     +-----------+-------------+
     |           |             |
 SUPPORTED   UNSUPPORTED     UNKNOWN
     |           |             |
  Return    Repair once     Controlled
                 |          unavailable
                 v           response
             Verify again
                 |
       Supported answer or
       transparent limitation
```

Direct answers skip source verification and still pass applicable output checks. Retrieval NONE and UNKNOWN remain on their existing terminal paths.

Count answer_repairs_used from zero, incrementing when scheduling repair, with a hard maximum of one. Maximum normal evidence path: two generation calls and two verification calls. A correction of malformed generation also consumes this allowance; do not create separate retry budgets that multiply calls.

Repair uses the original question, unchanged generation snapshot, original draft and bounded judge feedback. Remove or correct unsupported claims and retain supported facts. Do not restart the router, rewrite retrieval queries or search again. If repair still fails, return a controlled limitation response without presenting the rejected draft as verified.

UNKNOWN defaults to a controlled verification-unavailable response. An optional product mode may expose an unverified draft only if the API and UI explicitly label it unverified; that mode is out of the default implementation. A timeout is not evidence of either truth or hallucination.

# Output checks and user delivery

Normalize and scrub generated output before the support check so the judge evaluates the user-facing factual text. Run deterministic reference validation and safety/output checks on every returned path, including direct and terminal responses. If later scrubbing materially changes claims or references, invalidate verification rather than reusing an approval for different text.

Add an optional verification_status field to the public response. Use is_grounded=true only for SUPPORTED, false for UNSUPPORTED, and null for UNKNOWN or SKIPPED where compatible with the response schema. Migrate graph types and frontend badges accordingly. Deprecated NLI fields must not carry invented scores; use null or omit when unavailable. Operational success, refusal and missing-evidence responses must not be called source-verified merely because they are safe templates.

Keep the existing HTTP request and response flow initially. Do not stream unchecked factual answer tokens and then label them verified. Immediate progress feedback can describe generation or verification, without exposing private text or internal prompts. Token streaming and new transport protocols are deferred.

# Latency and cost controls

Use bounded evidence and recent history, a concise default answer-length budget, reusable clients and an overall answer-stage deadline that includes initial generation, checks and any repair. Per-operation timeouts and SDK retries must fit inside that deadline. Stop when insufficient time remains; do not launch work after the deadline.

Keep the successful path to one generation and one verification request. Do not add a model call just to decide generator complexity initially. Track total request cost and retries, not merely one provider call. A missing-evidence template avoids unnecessary generation and verification.

# Implementation locations

| Location | Change |
| --- | --- |
| backend/services/generation.py | Typed generation result, prompts, route behavior, evidence snapshot and support mapping. |
| backend/services/verification.py | Explicit verification outcomes and validated support checks; remove permissive error fallbacks. |
| backend/providers/groq.py | Provider invocation and structured result support without domain policy. |
| backend/providers/gemini.py | Optional Gemini adapter and lifecycle consistent with the existing provider boundary. |
| backend/providers/typesafe.py | Shared transport if Jev verification is enabled later. |
| backend/workflows/crag/nodes/generation.py | One generation attempt, bounded repair and controlled generation errors. |
| backend/workflows/crag/nodes/verification.py | Verdict handling, no false verification on errors or skipped checks. |
| backend/workflows/crag/edges.py and state.py | Deterministic transitions, repair count, statuses, snapshot and deadline. |
| backend/api/schemas/chat.py and api/chat.py | Backward-compatible status fields and output processing. |
| frontend/app/components/ChatMessage.tsx and related types | Display verification status truthfully if the interface exposes it. |
| backend/config.py and .env.example | Provider/model configuration, deadlines, token limits and rollback. |
| backend/tests/unit and tests/integration | Contract, bounded graph and HTTP regressions. |
| backend/docs | Setup and architecture updates. |

# Acceptance checks

- Sufficient evidence produces a supported answer without a second generation call.
- A supported partial answer names gaps and does not invent the missing facts.
- A fabricated fact or contradicted claim triggers one repair and at most one recheck.
- Repair preserves supported content and uses the same evidence snapshot.
- Invalid evidence IDs and unsupported source mappings cannot pass verification.
- Document, web and hybrid claims are checked against the appropriate evidence.
- Private policy gaps remain gaps despite unrelated public information.
- Direct answers receive SKIPPED, never a false verified label.
- Generation and judge failures return typed errors or UNKNOWN, not ordinary successful answers.
- Empty evidence, empty answers, malformed responses and nonfinite scores cannot produce SUPPORTED.
- Exhausted repair or deadline budgets terminate without restarting retrieval.
- The default delivery path does not expose rejected or unchecked drafts.
- Every response path passes output checks and frontend badges match API status.
- Existing routing and retrieval behavior, endpoints and relevant regression tests remain intact.

# Model comparison and completion criteria

Use a fixed set of roughly 30–50 labelled examples covering single-passage facts, multiple-passage synthesis, partial evidence, contradictions, missing answers, public web context and benign direct requests. Review a human-labelled subset of the verifier's judgments separately from generator quality. Avoid evaluating a model only with its own judgments.

Measure answer correctness, evidence support, citation support, false approvals, false rejections, repair rate, timeouts, median and p95 complete response latency, input/output usage and total cost per completed answer. Record provider and pinned model identities. Select the cheapest configuration that meets explicitly agreed quality and latency targets; do not claim the candidate is faster or better before measurements.

Completion means the typed contracts, bounded graph, corrected verification status, setup documentation and focused tests are implemented. Live quality and speed claims additionally require configured credentials and a completed comparison. Later guardrail and evaluation-framework rewrites build on these contracts.

# Related work

[Router rebuild plan](https://chatgpt.com/space/page_79b4f4246f688191925b909aeb48265b). Local prerequisites are .agents/spec/jev_router_spec.md and .agents/spec/jev_retrieval_spec.md. Use backend/docs/architecture.md for the current module layout.

