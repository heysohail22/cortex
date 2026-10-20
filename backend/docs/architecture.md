# Backend architecture

Cortex keeps HTTP handling, workflow orchestration, application policy and external integrations in separate packages. Start the backend from the `backend` directory; `main.py` and `config.py` remain at that root.

## Ownership

| Package | Owns |
| --- | --- |
| api | HTTP routes, status codes and public schemas |
| workflows/crag | Graph assembly, state, edges and retry orchestration |
| services | Application policy, prompts, generation, evidence assessment and history budgeting |
| providers | TypeSafe client lifecycle and calls, Groq model construction, Tavily requests |
| retrieval | Embeddings, scoped vector search, evidence preparation, parsing and indexing |
| repositories | Shared Supabase client, document metadata, conversations and raw-file storage |
| guardrails | Input, ingestion, output, PII checks |
| evals | Datasets, metric scoring, benchmark execution and reports |
| tests/unit | Isolated logic and mocked graph/provider tests |
| tests/integration | HTTP contracts and ingestion boundary tests |

## Dependencies

HTTP handlers invoke the workflow and application services. Nodes call specific services; edges remain deterministic. Services own the questions and thresholds while providers own SDK setup and request transport. Retrieval prepares evidence and preserves the existing session-scoped RPC. Repositories never import services or graph code.

Avoid importing all services from `services/__init__.py`: import the owning module directly. This keeps package imports from constructing unrelated models. Node exports in `workflows/crag/nodes/__init__.py` exist for graph assembly; mock a dependency in the specific node module where it is used.

Conversation persistence is in `repositories/conversations.py`; budgeting and summarization are in `services/conversations.py`. Parsing and structural topic extraction live in `retrieval/ingestion/parsing.py`, safety-aware chunk preparation in `chunking.py`, and persistence orchestration in `indexing.py`.

The refactor preserves model choices, temperatures, thresholds, API shapes, search scopes and retry behavior. It does not add authentication or change the database schema. Answer generation now uses typed contracts in `services/answer_contracts.py`, with an exact evidence snapshot and one shared repair allowance. See [generation and verification](generation_verification.md) for the status and failure policy.

## Module migration map

Older implementation specifications under `.agents/spec/` refer to these former locations. Use this map when implementing follow-up work.

| Former location | Current owner |
| --- | --- |
| crag/graph.py, state.py, edges.py | workflows/crag/ |
| crag/nodes.py | workflows/crag/nodes/router.py, generation.py, verification.py and web.py |
| crag/retrieval_nodes.py | workflows/crag/nodes/retrieval.py |
| services/router_service.py | services/routing.py |
| services/jev_service.py | providers/typesafe.py for transport; services/routing.py and evidence.py for policy |
| services/evaluator_service.py | services/evidence.py and retrieval/evidence.py |
| services/search_service.py | services/query_rewriting.py and providers/tavily.py |
| services/generator_service.py | services/generation.py |
| services/groundedness_service.py | services/verification.py |
| services/llm_service.py | services/direct_answers.py |
| services/conversation_service.py | services/conversations.py and repositories/conversations.py |
| rag/document_processor.py | retrieval/ingestion/parsing.py, chunking.py and indexing.py |
| rag/vector_store.py | retrieval/vector_store.py for vector work; repositories/documents.py for metadata; repositories/client.py for the client |
| rag/embeddings.py | retrieval/embeddings.py |
| rag/storage_service.py | repositories/storage.py |
| guardrails/prompt_guard.py | guardrails/input.py |
| guardrails/ingestion_guard.py | guardrails/ingestion.py |
| guardrails/output_guard.py | guardrails/output.py |
| guardrails/pii_redactor.py | guardrails/pii.py |
| evals/dataset.py | evals/datasets/samples.py |
| evals/evaluator.py | evals/metrics/scoring.py |
| evals/data/ | evals/datasets/data/ |
| tests/test_*.py | tests/unit/ and tests/integration/ |
| JEV_ROUTER.md, JEV_RETRIEVAL.md | docs/jev_router.md, docs/jev_retrieval.md |

The former Python import paths are replaced, not retained as aliases. Update external scripts to use the new modules. `main:app`, `python -m evals.runner` and `python -m evals.eval_router` remain the application and evaluation entry points. `langgraph.json` targets `./workflows/crag/graph.py:_crag_graph`.
