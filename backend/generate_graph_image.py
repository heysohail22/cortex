"""
Utility script to generate and save a beautiful visual diagram of the Cortex CRAG workflow.

Outputs:
  - crag_workflow_graph.png (High-resolution dark-mode image)
  - crag_workflow_graph.svg (Vector graphics for documentation / web)

Usage:
    uv run python generate_graph_image.py
    uv run python generate_graph_image.py --theme light
    uv run python generate_graph_image.py --raw
"""
from __future__ import annotations

import argparse
import base64
import os
import sys
import urllib.request
from pathlib import Path

from workflows.crag.graph import _crag_graph

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_PNG_PATH = BASE_DIR / "cortex_nli_workflow_graph.png"
DEFAULT_SVG_PATH = BASE_DIR / "cortex_nli_workflow_graph.svg"


def build_crag_mermaid(theme: str = "dark") -> str:
    """Construct a styled, production-ready architecture diagram of the Cortex CRAG system with NLI Groundedness."""
    is_dark = theme == "dark"
    bg_color = "#0b0f19" if is_dark else "#ffffff"
    text_color = "#f8fafc" if is_dark else "#0f172a"
    line_color = "#94a3b8" if is_dark else "#475569"

    return f"""%%{{init: {{
  'theme': 'base',
  'themeVariables': {{
    'darkMode': {str(is_dark).lower()},
    'background': '{bg_color}',
    'primaryColor': '#1e293b',
    'primaryTextColor': '{text_color}',
    'primaryBorderColor': '#38bdf8',
    'lineColor': '{line_color}',
    'secondaryColor': '#334155',
    'tertiaryColor': '#1e293b',
    'fontFamily': 'Inter, system-ui, -apple-system, sans-serif',
    'fontSize': '13px'
  }}
}}}}%%
flowchart TD
    classDef inputStyle fill:#1e3a8a,stroke:#60a5fa,stroke-width:2px,color:#ffffff,font-weight:700;
    classDef guardStyle fill:#450a0a,stroke:#f87171,stroke-width:2px,color:#fca5a5,font-weight:600;
    classDef routerStyle fill:#3b0764,stroke:#c084fc,stroke-width:2.5px,color:#ffffff,font-weight:700;
    classDef retrieveStyle fill:#064e3b,stroke:#34d399,stroke-width:2px,color:#ffffff,font-weight:600;
    classDef evalStyle fill:#78350f,stroke:#fbbf24,stroke-width:2.5px,color:#ffffff,font-weight:700;
    classDef webStyle fill:#164e63,stroke:#22d3ee,stroke-width:2px,color:#ffffff,font-weight:600;
    classDef genStyle fill:#581c87,stroke:#e879f9,stroke-width:2px,color:#ffffff,font-weight:600;
    classDef judgeStyle fill:#831843,stroke:#f472b6,stroke-width:2.5px,color:#ffffff,font-weight:700;
    classDef safeStyle fill:#14532d,stroke:#4ade80,stroke-width:2px,color:#ffffff,font-weight:600;
    classDef endStyle fill:#064e3b,stroke:#22c55e,stroke-width:2.5px,color:#ffffff,font-weight:700;

    subgraph Layer1 ["1. Ingress Security & Safety (Fast 0-20ms)"]
        UserReq(["💬 User Query"]):::inputStyle
        RateLimiter["⏱️ Sliding-Window Rate Limiter<br/><i>In-Memory IP + Session (0 tokens)</i>"]
        PromptGuard{{"🛡️ Tiered Prompt Guard<br/><i>Regex + Llama-Prompt-Guard-86M</i>"}}:::guardStyle
        PIIRedactor["🔒 PII Redactor<br/><i>Masks Secrets, Emails, API Keys</i>"]
        BlockNotice["🚫 Security Refusal Response"]:::guardStyle
    end

    subgraph Layer2 ["2. Intent Routing & Gatekeeper"]
        RouterNode{{"🎯 Intent Router & Direct Responder<br/><i>Groq Fast LLM (20b)</i>"}}:::routerStyle
        DirectWeb["🌐 Direct Web Search Node<br/><i>Live News, Current Events</i>"]:::webStyle
    end

    subgraph Layer3 ["3. Vector Database Retrieval"]
        VectorSearch["📚 Cosine Similarity Search<br/><i>Top-K Chunks via Gemini (768d) & Supabase pgvector</i>"]:::retrieveStyle
    end

    subgraph Layer4 ["4. Corrective RAG (CRAG) Evaluation Gate"]
        RetrievalEval{{"⚖️ CRAG Evaluator<br/><i>Grades Chunks & Bundles Query Rewriting</i>"}}:::evalStyle
        CRAGWebSearch["🔎 Tavily Web Search Node<br/><i>Fallback / Hybrid Augmentation</i>"]:::webStyle
    end

    subgraph Layer5 ["5. Generation & NLI Groundedness Verification"]
        AnswerGen["📝 Generator Node<br/><i>Context-Budgeted Groq 120b</i>"]:::genStyle
        NLIJudge{{"🧪 NLI Groundedness Judge<br/><i>Entailment Fact-Checker</i>"}}:::judgeStyle
        StrictRetryGen["⚠️ Strict Constrained Generator<br/><i>Temperature 0.0 Retry</i>"]:::genStyle
        SafeFallback["📋 Safe Refusal & Verbatim Fallback<br/><i>Zero-Hallucination Safe Fallback</i>"]:::safeStyle
    end

    subgraph Layer6 ["6. Egress & Output Security"]
        OutputGuard["🧹 Output Guard<br/><i>Secret Scrubbing & Format Verification</i>"]
        FinalStream(["✨ Verified Answer Stream to Client"]):::endStyle
    end

    %% Ingress Flow
    UserReq --> RateLimiter --> PromptGuard
    PromptGuard -->|"Unsafe / Injection"| BlockNotice --> FinalStream
    PromptGuard -->|"Safe"| PIIRedactor --> RouterNode

    %% Routing Flow
    RouterNode -->|"direct_answer (Direct LLM reply)"| OutputGuard
    RouterNode -->|"web_search"| DirectWeb --> AnswerGen
    RouterNode -->|"rag"| VectorSearch

    %% Vector Search to Evaluator
    VectorSearch --> RetrievalEval

    %% CRAG Evaluation Branching
    RetrievalEval -->|"CORRECT (Sufficient Context)"| AnswerGen
    RetrievalEval -->|"INCORRECT: Attempt 1 (Rewritten Query)"| VectorSearch
    RetrievalEval -->|"INCORRECT: Retry Exhausted (Web Fallback)"| CRAGWebSearch
    RetrievalEval -->|"AMBIGUOUS (Partial Chunks + Web Augment)"| CRAGWebSearch
    CRAGWebSearch --> AnswerGen

    %% Generation & NLI Groundedness Flow
    AnswerGen --> NLIJudge
    NLIJudge -->|"Entailment (Grounded >= 0.85)"| OutputGuard --> FinalStream
    NLIJudge -->|"Contradiction / Neutral: Attempt 1"| StrictRetryGen --> NLIJudge
    NLIJudge -->|"Contradiction / Neutral: Retry Exhausted"| SafeFallback --> FinalStream
"""


def render_mermaid_ink(mermaid_code: str, output_path: Path, fmt: str = "png", bg_color: str = "0b0f19") -> bool:
    """Fetch rendered diagram from Mermaid.ink API and save to disk."""
    try:
        b64 = base64.b64encode(mermaid_code.encode("utf-8")).decode("ascii")
        if fmt == "svg":
            url = f"https://mermaid.ink/svg/{b64}"
        else:
            url = f"https://mermaid.ink/img/{b64}?bgColor={bg_color}"

        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Cortex CLI)"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
            output_path.write_bytes(data)
            return True
    except Exception as e:
        print(f"Warning: Failed to render {fmt.upper()} via Mermaid.ink: {e}", file=sys.stderr)
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate visual diagram for Cortex CRAG workflow.")
    parser.add_argument(
        "--theme",
        choices=["dark", "light"],
        default="dark",
        help="Visual color theme (default: dark)",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Render raw LangGraph runtime graph instead of the enhanced architecture diagram",
    )
    args = parser.parse_args()

    print(f"🎨 Generating visual graph diagram (theme: {args.theme})...")

    if args.raw:
        # Fallback to standard LangGraph draw_mermaid_png
        try:
            png_bytes = _crag_graph.get_graph().draw_mermaid_png()
            DEFAULT_PNG_PATH.write_bytes(png_bytes)
            print(f"✓ Raw LangGraph image saved to: {DEFAULT_PNG_PATH}")
        except Exception as e:
            print(f"Error rendering raw LangGraph PNG: {e}", file=sys.stderr)
        return

    mermaid_syntax = build_crag_mermaid(theme=args.theme)
    bg_hex = "0b0f19" if args.theme == "dark" else "ffffff"

    # Render PNG
    png_success = render_mermaid_ink(mermaid_syntax, DEFAULT_PNG_PATH, fmt="png", bg_color=bg_hex)
    if png_success:
        print(f"✓ High-res PNG saved to: {DEFAULT_PNG_PATH}")

    # Render SVG
    svg_success = render_mermaid_ink(mermaid_syntax, DEFAULT_SVG_PATH, fmt="svg")
    if svg_success:
        print(f"✓ Scalable SVG saved to: {DEFAULT_SVG_PATH}")

    if not png_success and not svg_success:
        print("Falling back to local LangGraph renderer...")
        try:
            png_bytes = _crag_graph.get_graph().draw_mermaid_png()
            DEFAULT_PNG_PATH.write_bytes(png_bytes)
            print(f"✓ Local LangGraph image saved to: {DEFAULT_PNG_PATH}")
        except Exception as e:
            print(f"Local fallback also failed: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
