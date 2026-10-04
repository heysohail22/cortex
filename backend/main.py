import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


from api.chat import router as chat_router
from api.documents import router as documents_router

app = FastAPI(
    title="Cortex API",
    description="Multi-Agent RAG Application — powered by Groq, Supabase & Tavily",
    version="1.0.0",
)

# ── CORS (Next.js frontend) ───────────────────────────────────────────────────
origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://3.25.64.38:3001",
    "https://cortex-ai.duckdns.org",
    "http://cortex-ai.duckdns.org",
    "https://cortex-lime-zeta.vercel.app",
]

# Allow custom frontend URL from env if configured
custom_frontend = os.getenv("FRONTEND_URL")
if custom_frontend and custom_frontend not in origins:
    origins.append(custom_frontend)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(chat_router)
app.include_router(documents_router)


# ── Health & root ─────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "Cortex Multi-Agent RAG API",
        "version": "1.0.0",
    }


@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("ENVIRONMENT", "development").lower() == "development"
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=reload)
