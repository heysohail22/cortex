import os
from pathlib import Path
from dotenv import load_dotenv

_env_file = Path(__file__).resolve().parent / ".env"
if _env_file.exists():
    load_dotenv(_env_file)
else:
    load_dotenv()

# Groq LLMs for generation, evaluation, judging and explicit routing rollback
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
GROQ_REASONING_MODEL = os.getenv("GROQ_REASONING_MODEL", "openai/gpt-oss-120b")
GROQ_FAST_MODEL = os.getenv("GROQ_FAST_MODEL", "openai/gpt-oss-20b")

# Supabase (vector store + future auth & sessions)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Google Gemini (cloud embeddings — no local model, no RAM spikes)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_EMBEDDING_MODEL = "gemini-embedding-001"

# Chunking config
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Retrieval config
TOP_K_RESULTS = 5
SIMILARITY_THRESHOLD = 0.3

# ── Layer 1: Frontline Guardrails Configuration ──────────────────────────────
# Rate Limiting & Throttling (increased ceiling to prevent benchmark bottlenecks)
ENABLE_RATE_LIMITING = os.getenv("ENABLE_RATE_LIMITING", "true").lower() in ("true", "1")
RATE_LIMIT_CHAT_REQUESTS = int(os.getenv("RATE_LIMIT_CHAT_REQUESTS", "100"))
RATE_LIMIT_CHAT_WINDOW = int(os.getenv("RATE_LIMIT_CHAT_WINDOW", "60"))
RATE_LIMIT_UPLOAD_REQUESTS = int(os.getenv("RATE_LIMIT_UPLOAD_REQUESTS", "10"))
RATE_LIMIT_UPLOAD_WINDOW = int(os.getenv("RATE_LIMIT_UPLOAD_WINDOW", "60"))

# Prompt Injection & Jailbreak Defense
ENABLE_PROMPT_GUARD = os.getenv("ENABLE_PROMPT_GUARD", "true").lower() in ("true", "1")
USE_LOCAL_PROMPT_GUARD_MODEL = os.getenv("USE_LOCAL_PROMPT_GUARD_MODEL", "false").lower() in ("true", "1")
PROMPT_GUARD_MODEL = os.getenv("PROMPT_GUARD_MODEL", "meta-llama/Prompt-Guard-86M")
PROMPT_GUARD_THRESHOLD = float(os.getenv("PROMPT_GUARD_THRESHOLD", "0.6"))

# PII & Sensitive Data Redaction
ENABLE_PII_REDACTION = os.getenv("ENABLE_PII_REDACTION", "true").lower() in ("true", "1")
ENABLE_PRESIDIO_NER = os.getenv("ENABLE_PRESIDIO_NER", "false").lower() in ("true", "1")

# Document Ingestion Security
ENABLE_INGESTION_GUARD = os.getenv("ENABLE_INGESTION_GUARD", "true").lower() in ("true", "1")

# ── Per-Node Execution Timeouts (Seconds) ────────────────────────────────────
TIMEOUT_ROUTER = float(os.getenv("TIMEOUT_ROUTER", "15.0"))
TIMEOUT_RETRIEVAL = float(os.getenv("TIMEOUT_RETRIEVAL", "4.0"))
TIMEOUT_RETRIEVAL_EVAL = float(os.getenv("TIMEOUT_RETRIEVAL_EVAL", "5.0"))
TIMEOUT_WEB_SEARCH = float(os.getenv("TIMEOUT_WEB_SEARCH", "5.0"))
TIMEOUT_GENERATION = float(os.getenv("TIMEOUT_GENERATION", "12.0"))
TIMEOUT_GROUNDEDNESS = float(os.getenv("TIMEOUT_GROUNDEDNESS", "5.0"))

# ── Context Token Budget & Length Ceilings (Characters) ──────────────────────
MAX_DOC_CONTEXT_CHARS = int(os.getenv("MAX_DOC_CONTEXT_CHARS", "10000"))      # ~2,500 tokens
MAX_WEB_CONTEXT_CHARS = int(os.getenv("MAX_WEB_CONTEXT_CHARS", "5000"))       # ~1,250 tokens
MAX_WEB_SNIPPET_CHARS = int(os.getenv("MAX_WEB_SNIPPET_CHARS", "800"))        # ~200 tokens per snippet
MAX_HYBRID_DOC_CHARS = int(os.getenv("MAX_HYBRID_DOC_CHARS", "7000"))         # ~1,750 tokens
MAX_HYBRID_WEB_CHARS = int(os.getenv("MAX_HYBRID_WEB_CHARS", "3500"))         # ~875 tokens

# ── Conversation Memory & Summarization ────────────────────────────────────────
MAX_CONVERSATION_TOKENS = int(os.getenv("MAX_CONVERSATION_TOKENS", "4000"))  # Token budget for prior context
MAX_RECENT_MESSAGES = int(os.getenv("MAX_RECENT_MESSAGES", "2"))             # Keep last N messages verbatim

# Jev routing. Set ROUTER_PROVIDER=groq for explicit rollback.
ROUTER_PROVIDER = os.getenv("ROUTER_PROVIDER", "jev").lower()
TYPESAFE_API_KEY = os.getenv("TYPESAFE_API_KEY")
JEV_MODEL = os.getenv("JEV_MODEL", "jev-latest")
TIMEOUT_JEV = float(os.getenv("TIMEOUT_JEV", "5.0"))
JEV_MAX_RETRIES = int(os.getenv("JEV_MAX_RETRIES", "0"))
JEV_SAFETY_THRESHOLD = float(os.getenv("JEV_SAFETY_THRESHOLD", "0.7"))
JEV_REVIEW_THRESHOLD = float(os.getenv("JEV_REVIEW_THRESHOLD", "0.35"))
JEV_INTENT_CONFIDENCE = float(os.getenv("JEV_INTENT_CONFIDENCE", "0.6"))
MAX_CONCURRENT_CHATS = int(os.getenv("MAX_CONCURRENT_CHATS", "8"))

# Retrieval correction: one attempt is enforced in graph code.
TIMEOUT_RETRIEVAL_STAGE = float(os.getenv("TIMEOUT_RETRIEVAL_STAGE", "25"))
TIMEOUT_RETRIEVAL_REWRITE = float(os.getenv("TIMEOUT_RETRIEVAL_REWRITE", "4"))
MAX_EVIDENCE_CONTEXT_CHARS = int(os.getenv("MAX_EVIDENCE_CONTEXT_CHARS", "8000"))
MAX_EVIDENCE_PASSAGE_CHARS = int(os.getenv("MAX_EVIDENCE_PASSAGE_CHARS", "2000"))
MAX_EVIDENCE_CANDIDATES = int(os.getenv("MAX_EVIDENCE_CANDIDATES", "10"))
# Excludes uncertain as well as high-risk passages. Calibrate before deployment.
JEV_EVIDENCE_INJECTION_MAX = float(os.getenv("JEV_EVIDENCE_INJECTION_MAX", "0.35"))

# Answer generation and independent verification. Groq remains the baseline.
GENERATION_PROVIDER = os.getenv("GENERATION_PROVIDER", "groq").lower()
GENERATION_MODEL = os.getenv("GENERATION_MODEL", GROQ_REASONING_MODEL)
GENERATION_TEMPERATURE = float(os.getenv("GENERATION_TEMPERATURE", "0.2"))
GENERATION_REASONING = os.getenv("GENERATION_REASONING", "") or None
VERIFICATION_MODEL = os.getenv("VERIFICATION_MODEL", GROQ_REASONING_MODEL)
VERIFICATION_REASONING = os.getenv("VERIFICATION_REASONING", "") or None
ANSWER_PROVIDER_RETRIES = int(os.getenv("ANSWER_PROVIDER_RETRIES", "0"))
MAX_ANSWER_OUTPUT_TOKENS = int(os.getenv("MAX_ANSWER_OUTPUT_TOKENS", "1600"))
MAX_VERIFICATION_OUTPUT_TOKENS = int(os.getenv("MAX_VERIFICATION_OUTPUT_TOKENS", "1800"))
MAX_ANSWER_CHARS = int(os.getenv("MAX_ANSWER_CHARS", "8000"))
MAX_ANSWER_CLAIMS = int(os.getenv("MAX_ANSWER_CLAIMS", "24"))
MAX_GENERATION_CONTEXT_CHARS = int(os.getenv("MAX_GENERATION_CONTEXT_CHARS", "12000"))
TIMEOUT_ANSWER_STAGE = float(os.getenv("TIMEOUT_ANSWER_STAGE", "35"))
