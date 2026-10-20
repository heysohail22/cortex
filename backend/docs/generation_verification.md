# Generation and answer verification

The answer path uses a typed candidate, precise evidence references, an independent support check and at most one repair. Support means faithful to the supplied evidence; it does not establish the absolute truth or freshness of the source.

## Request flow

Generation sees the original question, bounded recent history, selected passages, gaps and conflicts. History and passages are untrusted data. A single context-budget pass creates a snapshot with stable IDs, source kinds and exact text. The same snapshot is used by generation, verification and repair. Truncation downgrades completeness to PARTIAL and is disclosed to the model.

The generator returns answer text and claim-to-evidence mappings. Application code scrubs text before checking support, validates claim spans and IDs, and maps only cited IDs to public filenames or URLs. A known citation ID is not proof of semantic support. The judge checks the entire answer, all submitted claims, source attribution, omitted factual claims and whether known gaps were honestly acknowledged.

A successful evidence path uses one generation call and one verification call. UNSUPPORTED can trigger one repair with the same snapshot and bounded feedback. Malformed candidate correction uses that same repair allowance. UNKNOWN does not start another call chain. No answer repair restarts retrieval or web search.

## Status and delivery

| Status | Public behavior |
| --- | --- |
| SUPPORTED | Return the checked answer and validated citations; is_grounded=true. |
| UNSUPPORTED after repair | Return a limitation response without the rejected draft or citations; is_grounded=false. |
| UNKNOWN | Return a temporary unavailable response without the unchecked draft; is_grounded=null. |
| SKIPPED | Direct or deterministic terminal response; is_grounded=null, with no source-verification claim. |

Generation separately reports SUCCESS, ERROR or TIMEOUT. Provider exceptions and malformed responses are not ordinary factual answers. Deprecated nli_score is null; actual judge confidence is retained internally without pretending it is a calibrated entailment score.

Web and hybrid answers are checked against their web/document snapshot, rather than skipping the judge. Public sources cannot establish missing private company policy. Direct answers do not get invented citations. Empty evidence produces a limitation instead of a model answer.

Output checks run on all API response paths. If final API processing changes approved text or citations, the approval is invalidated and the user receives a controlled response. The active frontend shows Supported by sources, Verification unavailable, Answer could not be supported, or Source check not applicable. Older saved messages with no status show Not checked. Factual tokens are not streamed before verification.

## Provider configuration

Groq remains the default. The TypeSafe router and evidence-assessment settings are independent from answer-model settings. No automatic provider or expensive-model fallback is enabled.

```dotenv
GENERATION_PROVIDER=groq
GENERATION_MODEL=openai/gpt-oss-120b
GENERATION_TEMPERATURE=0.2
GENERATION_REASONING=
VERIFICATION_MODEL=openai/gpt-oss-120b
VERIFICATION_REASONING=
ANSWER_PROVIDER_RETRIES=0
MAX_ANSWER_OUTPUT_TOKENS=1600
MAX_VERIFICATION_OUTPUT_TOKENS=1800
MAX_ANSWER_CHARS=8000
MAX_ANSWER_CLAIMS=24
MAX_GENERATION_CONTEXT_CHARS=12000
```

Application stage deadlines and operation timeouts have been removed. The single repair allowance remains. Provider reasoning settings are omitted by default; set only values supported by the selected model. Output limits include provider-specific reasoning overhead where the provider charges/counts it that way. Tune with measured complete response time rather than throughput alone.

The optional Gemini generator uses the existing server-side GEMINI_API_KEY. Set both provider and model explicitly:

```dotenv
GENERATION_PROVIDER=gemini
GENERATION_MODEL=gemini-3.5-flash-lite
```

The current Google catalogue lists this candidate, but account availability and comparative quality are not established by documentation. Check models available to your account and pin the chosen ID. The independent verifier remains Groq; keep GROQ_API_KEY configured even when using Gemini for generation. Restore the Groq settings to roll back the generator without removing honest verification outcomes.

New provider clients are lazy and reused, with cleanup on application shutdown. The direct Groq SDK and google-genai requirements and uv lockfile record versions supporting the tested request structures. API keys remain in .env, never frontend configuration.

## Comparison command

The fixed dataset has 32 synthetic cases covering document facts, combined evidence, partial evidence, conflicts, public snippets, hybrid attribution and direct requests. Existing synthetic Novacore references are reused alongside additional fixtures. Reference expectations require human review; model judge approval is not ground truth.

Dry-run validation makes zero model requests:

```bash
python -m evals.compare_generation \
  --candidate groq:openai/gpt-oss-120b \
  --candidate gemini:gemini-3.5-flash-lite \
  --dry-run
```

Remove --dry-run to run paid provider calls. Start with --limit 2 to check account access before a full run. The command uses identical snapshots, questions and output limits across candidates, with the production verification and repair policy. It does not write to the vector database or invoke the router. Run it as a standalone process, not inside the API server, because it changes process-local model configuration sequentially.

The report includes actual provider model identities, raw usage, attempts, repair counts, median/p95 complete answer latency, statuses and reference answers for human review. It leaves human_review empty. Human reviewers should score correctness, claim/citation support and judge false approvals or rejections separately. Review rejected drafts through controlled internal evaluation when measuring false rejections; they are not delivered to users.

Optional --rates-json accepts rates keyed by actual provider:model response identities, with input_per_million, output_per_million and cached_input_per_million when caching is used. Supply current rates from the provider, not estimates copied from an old document. Missing usage, model rates or cache rates yields unknown cost, never zero. Gemini output estimates include reported thinking tokens. Failed requests may have unreported charges; compare provider billing before treating estimates as authoritative.

This implementation does not claim a model quality or speed improvement. Live comparisons, rate calibration and human-reviewed quality thresholds remain required before changing the default.

## Verification

Run the backend suite from backend:

```bash
.venv/bin/python -m pytest tests/ -q
```

Tests cover transport request formats, exact snapshots, semantic-verdict handling, citation IDs, source kinds, skipped checks, timeouts, invalid provider output, one shared repair budget, context truncation, web/hybrid paths and post-verification scrubbing. Mock tests establish integration behavior rather than real model accuracy.

Frontend checks remain pnpm lint and pnpm build. The production build fetches the existing Google font and therefore needs network access.

## Official references

- [Groq structured output and supported models](https://console.groq.com/docs/structured-outputs)
- [Google structured outputs](https://ai.google.dev/gemini-api/docs/structured-output)
- [Google model catalogue](https://ai.google.dev/gemini-api/docs/models)
- [Google pricing](https://ai.google.dev/gemini-api/docs/pricing)

The API shapes were also checked against the installed SDKs. Live account access, provider billing and safety accuracy require separate verification.
