# Cortex — AI Agent Project Guide

This file is a concise reference for AI coding agents working on **Cortex**, a multi-agent Retrieval-Augmented Generation (RAG) application. It covers the project architecture, technology stack, code organization, build/test commands, development conventions, and security considerations.

---

## Project Overview

Cortex is a full-stack AI assistant that routes user questions across three execution paths:

1. **Document RAG** — answers from uploaded PDF, DOCX, TXT, and Markdown files.
2. **Real-time Web Search** — fetches live information from the web.
3. **Direct LLM Knowledge** — answers general knowledge, coding, and math questions without retrieval.

The backend is implemented in Python with **FastAPI** and **LangGraph**, and the frontend is a **Next.js 16 / React 19** chat UI. The system emphasizes:

- **Corrective RAG (CRAG)** — retrieval evaluation, query rewriting, and web fallback.
- **Multi-layer guardrails** — prompt injection defense, PII redaction, ingestion validation, output scrubbing, and citation verification.
- **Groundedness checking** — an independent LLM judge detects hallucinations and triggers strict retries.
- **Cloud-native embeddings** — Google Gemini `text-embedding-004` truncated to 768 dimensions via MRL, stored in Supabase `pgvector`.

---

## Repository Layout

```text
Cortex/
├── backend/
│   ├── api/                  # HTTP handlers and schemas/
│   ├── workflows/crag/       # Graph, state, edges and nodes/
│   ├── services/             # Routing, evidence, rewriting and generation policy
│   ├── providers/            # TypeSafe, Groq and Tavily adapters
│   ├── retrieval/            # Embeddings, vector search, evidence and ingestion/
│   ├── repositories/         # Supabase client, metadata, history and file storage
│   ├── guardrails/           # Input, ingestion, PII, output and rate limiting
│   ├── evals/                # datasets/, metrics/, runner and reports/
│   ├── tests/                # unit/ and integration/
│   ├── docs/                 # Architecture and setup guides
│   ├── config.py             # Environment configuration
│   ├── main.py               # FastAPI application entry point
│   ├── langgraph.json        # LangGraph CLI entry point
│   ├── Dockerfile
│   └── pyproject.toml
├── frontend/                 # Next.js chat UI
├── docker-compose.yml
├── AGENTS.md
└── README.md
```

---

## Technology Stack

### Backend

| Layer | Technology |
|---|---|
| Runtime | Python 3.12+ |
| Web Framework | FastAPI + Uvicorn |
| Agent Orchestration | LangGraph + LangChain |
| LLMs | Groq (`ChatGroq`) — reasoning and fast models |
| Embeddings | Google Gemini `embedding-001` (768-dim via MRL) |
| Vector Store | Supabase `pgvector` (via `match_document_chunks` RPC) |
| Web Search | Tavily API |
| Document Parsing | PyMuPDF, python-docx, docx2txt, LangChain text splitters |
| Evaluation | Custom LLM-as-a-judge metrics + RAGAS (optional) |
| Package Manager | `uv` (lockfile: `backend/uv.lock`) |

### Frontend

| Layer | Technology |
|---|---|
| Framework | Next.js 16.2.6 (App Router) |
| UI Library | React 19.2.4 |
| Styling | Tailwind CSS v4 (`@tailwindcss/postcss`) |
| Icons | Inline SVGs |
| Package Manager | `pnpm` |
| Linting | ESLint 9 with `eslint-config-next` |

---

## Code Organization

### Backend Modules

- `api/chat.py` and `api/documents.py`: HTTP handlers; public models live in `api/schemas/`.
- `workflows/crag/graph.py`: graph assembly and `run_crag_async` / `run_crag` entry points.
- `workflows/crag/state.py` and `edges.py`: workflow state and deterministic branching.
- `workflows/crag/nodes/`: separate router, retrieval, generation, verification and web nodes.
- `services/routing.py`: intent and safety policies, including explicit Groq rollback.
- `services/evidence.py`: typed evidence assessment and passage policy.
- `services/query_rewriting.py`: conditional retrieval and web query rewriting.
- `services/generation.py`, `verification.py`, `direct_answers.py`: answer prompts and checks.
- `services/conversations.py`: history budgeting and summarization.
- `providers/typesafe.py`, `groq.py`, `tavily.py`: external client integration.
- `retrieval/evidence.py`: stable chunk IDs, deduplication and context budgets.
- `retrieval/vector_store.py` and `embeddings.py`: scoped vector search and embeddings.
- `retrieval/ingestion/`: parsing, chunk preparation and indexing orchestration.
- `repositories/client.py`: shared Supabase client; `documents.py`, `conversations.py` and `storage.py` own persistence.
- `guardrails/`: `input.py`, `ingestion.py`, `output.py`, `pii.py` and `rate_limiter.py`.
- `evals/datasets/`: samples and static benchmark inputs; `evals/metrics/`: scoring.
- `docs/architecture.md`: dependency rules and migration map. Older `.agents/spec/` documents use pre-refactor paths; resolve them using this map.

### Frontend Structure

- **`app/page.tsx`** — Main chat page. Manages sessions, messages, document state, and backend communication.
- **`app/layout.tsx`** — Root layout with metadata and font preconnects.
- **`app/globals.css`** — Tailwind v4 theme, custom color tokens, animations, and utility classes.
- **`app/components/`** — React components:
  - `ChatInput.tsx` — Auto-resizing textarea with send/attach controls.
  - `ChatMessage.tsx` — Renders assistant messages with source badges and citations.
  - `Sidebar.tsx` — Chat history, new chat, and global knowledge base UI.
  - `DocumentUpload.tsx` / `DocumentList.tsx` — Upload and delete documents.
  - `SourceBadge.tsx` — Displays answer source (RAG, LLM, web, hybrid).

---

## Configuration

Backend configuration is environment-driven via `backend/.env`. Copy `backend/.env.example` to `backend/.env` and fill in the values.

Required keys:

```bash
GROQ_API_KEY=...                    # Groq API key
TAVILY_API_KEY=...                  # Tavily web search API key
SUPABASE_URL=...                    # Supabase project URL
SUPABASE_KEY=...                    # Supabase service role key
GEMINI_API_KEY=...                  # Google Gemini API key
```

Optional behavior toggles (all in `backend/config.py`):

```bash
GROQ_REASONING_MODEL=openai/gpt-oss-120b      # Main synthesis model
GROQ_FAST_MODEL=openai/gpt-oss-20b           # Router/evaluator/judge model
ENABLE_RATE_LIMITING=true
ENABLE_PROMPT_GUARD=true
ENABLE_PII_REDACTION=true
ENABLE_INGESTION_GUARD=true
LANGCHAIN_TRACING_V2=true                    # Optional: enable LangSmith tracing
LANGCHAIN_API_KEY=...                        # Only needed if LangSmith tracing enabled
LANGCHAIN_PROJECT=cortex
```

Frontend environment variable (in `frontend/.env.local`):

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Build and Run Commands

### Backend

The backend uses `uv` for dependency management and a local virtual environment at `backend/.venv`.

```bash
# Run the FastAPI dev server (reload on http://localhost:8000)
cd backend
uv run python main.py

# Or directly with the venv
backend/.venv/bin/python main.py

# Install/sync dependencies (if needed)
cd backend
uv sync
```

### Frontend

```bash
# Install dependencies
cd frontend
pnpm install

# Start the dev server (http://localhost:3000)
pnpm dev

# Production build
pnpm build

# Start production server
pnpm start

# Lint
pnpm lint
```

### LangGraph CLI

The CRAG graph is registered in `backend/langgraph.json`:

```bash
cd backend
langgraph dev
```

### Docker & Docker Compose

Run the full stack containerized:

```bash
# Build and run backend & frontend containers
docker compose up --build -d

# View service logs
docker compose logs -f

# Shut down containers
docker compose down
```


---

## Testing

### Backend Tests

Backend tests use `pytest` with the `asyncio_mode = auto` setting configured in `pyproject.toml`. Some tests also use the standard `unittest` module.

```bash
cd backend
uv run pytest tests/ -q

# Or with the venv directly
backend/.venv/bin/python -m pytest tests/ -q
```

Test files:

- `tests/unit/test_guardrails.py` — Rate limiting, prompt guard, PII redaction, ingestion guard.
- `tests/integration/test_api_guardrails.py` — FastAPI `TestClient` tests for health, chat blocking, and upload validation.
- `tests/unit/test_context_budget.py` — Context budget capping and web-result cleaning.
- `tests/unit/test_crag_reliability.py` — CRAG routing, loop bounds, and node timeout fallbacks.
- `tests/unit/test_eval_framework.py` — Evaluation dataset serialization and guardrail scoring.

### Evaluation Benchmark

Run the end-to-end evaluation suite from the backend root:

```bash
cd backend
uv run python -m evals.runner

# Custom dataset, category filter, or sample limit
uv run python -m evals.runner --dataset path/to/dataset.json --category fact_retrieval --samples 5
```

Reports are written to `backend/evals/reports/` as Markdown and CSV.

### Frontend Tests

There are currently no automated frontend tests in the repository. Manual verification is done by running `pnpm dev` and exercising the chat/document flows.

---

## Code Style and Conventions

### Python

- Use `from __future__ import annotations` at the top of files.
- Prefer `async`/`await` for I/O-bound work; wrap blocking calls with `asyncio.to_thread`.
- Use Pydantic `BaseModel` for structured LLM outputs.
- Keep business logic in `services/` and orchestration in `workflows/crag/`; routers in `api/` should be thin.
- All timeout values are centralized in `config.py` and applied per-node via `asyncio.wait_for`.
- Use module-level singletons for LLM clients and vector store clients (lazy initialization where possible).
- Guardrails are organized as classes with static/global helper functions.

### TypeScript / Frontend

- The project uses Next.js App Router with client components (`"use client"`) for interactive UI.
- Tailwind v4 theme tokens are defined in `app/globals.css` using `@theme`.
- Inline SVGs are used instead of icon libraries.
- `localStorage` is used for persistent session and user-id state on the client.

### Frontend Code Quality
- The frontend passes ESLint 9 (`pnpm lint`) and Next.js production builds (`pnpm build`) with zero errors.

---

## CRAG Workflow Summary

1. **Router** uses Jev for intent and separate safety assessments; uncertain or failed assessments stop before tools.
2. **Retrieve** fetches top-k chunks within the existing session scope.
3. **Evidence assessment** selects safe useful passages and returns SUFFICIENT, PARTIAL, NONE or UNKNOWN. Legacy API labels remain CORRECT, AMBIGUOUS, INCORRECT and UNKNOWN.
4. Partial or missing evidence can trigger one targeted rewrite and correction retrieval. Retain and deduplicate useful passages across attempts.
5. After correction, generate a supported full or partial answer, clarify, or return a missing-evidence response. Database/provider failures remain unavailable outcomes.
6. Public supplementation requires an explicit trusted policy and independently approved public query. Missing private facts never trigger automatic public web substitution.
7. **Generate** uses bounded context. The document groundedness judge permits one repair before safe fallback. Supplemental public evidence is explicitly unverified by that document-only judge.

Retry bounds live in `workflows/crag/edges.py` and `workflows/crag/nodes/retrieval.py`. See `backend/docs/jev_retrieval.md` for deadlines and known verification limitations.

---

## Security Considerations

- **API keys and secrets** live only in `backend/.env` and `frontend/.env.local`. These files are gitignored. Never commit them.
- **Prompt injection** is blocked by regex heuristics and an optional local Hugging Face classifier.
- **PII redaction** masks emails, phones, SSNs, IP addresses, credit cards, and common API keys before indexing and before sending queries to downstream services.
- **File upload validation** checks magic bytes, rejects executable payloads, and validates file-extension/header consistency.
- **Indirect prompt injection** in uploaded documents is scanned and quarantined at chunk level.
- **Output guardrails** scrub leaked secrets/system delimiters and verify citations against real sources.
- **Rate limiting** is applied per ASGI client identity on chat and upload endpoints using a sliding-window limiter.
- **CORS** in `main.py` is restricted to `localhost:3000` and the production Vercel deployment URL.

---

## Deployment

- **Frontend**: Designed for Vercel. The production URL is already configured in backend CORS (`https://cortex-lime-zeta.vercel.app`).
- **Backend**: Can be deployed as a container or via a Python process manager. Exposes Uvicorn on port `8000` by default. Ensure all required environment variables are set in the target environment.
- **Supabase**: Requires a `document_chunks` table with a `pgvector` column and the `match_document_chunks` RPC function.
- **LangGraph CLI**: The graph is registered in `langgraph.json` for LangGraph Platform deployments.

---

## Useful Files to Know

- `backend/main.py` — FastAPI app and middleware.
- `backend/config.py` — Central configuration.
- `backend/workflows/crag/graph.py` — CRAG workflow compiler and public runner.
- `backend/workflows/crag/edges.py` — Workflow routing and loop bounds.
- `backend/guardrails/__init__.py` — Public guardrail API surface.
- `backend/services/` — Application policy modules; import their functions explicitly.
- `frontend/app/page.tsx` — Main application page.
- `frontend/app/globals.css` — Design tokens and theme.
- `frontend/package.json` — Scripts and dependencies.

---

## Getting Started (Minimal)

1. Install backend dependencies:
   ```bash
   cd backend
   uv sync
   ```
2. Create `backend/.env` from `backend/.env.example` and fill in API keys.
3. Start the backend:
   ```bash
   uv run python main.py
   ```
4. In a new terminal, install and run the frontend:
   ```bash
   cd frontend
   pnpm install
   pnpm dev
   ```
5. Open `http://localhost:3000`.
