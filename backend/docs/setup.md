# Backend setup

Run commands from the `backend` directory.

```bash
uv sync
cp .env.example .env
```

Configure the provider credentials in `.env`. Never commit this file. Jev setup is described in [the router guide](jev_router.md), with retrieval options in [the retrieval guide](jev_retrieval.md) and answer configuration in [generation and verification](generation_verification.md).

```bash
# Development server
uv run python main.py

# Regression suite
uv run pytest tests/ -q

# Run only API and boundary tests
uv run pytest tests/integration/ -q

# LangGraph development server
uv run langgraph dev

# Evaluation CLI
uv run python -m evals.runner --help
uv run python -m evals.runner
```

The local virtual environment can be used directly, for example `.venv/bin/python -m pytest tests/ -q`. End-to-end evaluations call external providers and may create temporary evaluation documents; the regression tests mock those boundaries.

Container startup remains `uvicorn main:app --host 0.0.0.0 --port 8000`. Run `docker compose up --build -d` from the repository root to build the stack. No service ports or public HTTP endpoints changed in the folder refactor.
