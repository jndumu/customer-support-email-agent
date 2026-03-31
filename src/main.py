"""FastAPI application entry point.

APPLICATION ARCHITECTURE OVERVIEW:
─────────────────────────────────────────────────────────────────────────────
  HTTP Request
      │
      ▼
  FastAPI (src/main.py)
      │  CORS middleware → routes all /api/v1/* requests to api_router
      ▼
  API Router (src/api/v1/router.py)
      │  /api/v1/emails/*     → emails.py endpoints
      │  /api/v1/followups/*  → followups.py endpoints
      │  /api/v1/health       → health.py endpoint
      ▼
  POST /api/v1/emails/process
      │  Builds initial AgentState from request body
      │  Calls agent_graph.ainvoke(state)
      ▼
  LangGraph Pipeline (src/graph/agent_graph.py)
      │  ingest → classify → retrieve → draft → review → send
      │                              ↘ escalate ↗
      ▼
  EmailResponse returned to caller
─────────────────────────────────────────────────────────────────────────────

RUNNING THE APP:
  uv run uvicorn src.main:app --reload

API DOCS:
  http://localhost:8000/docs  (Swagger UI)
  http://localhost:8000/redoc (ReDoc)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.core.logging import configure_logging
from src.api.v1.router import api_router

# Configure structured logging before anything else
configure_logging()

app = FastAPI(
    title="Customer Support Email Agent",
    description=(
        "AI-powered email support agent using LangGraph, LangChain, and OpenAI. "
        "Classifies incoming emails, retrieves relevant knowledge, drafts responses, "
        "reviews quality, and escalates complex cases to human agents."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Allow all origins in development — restrict in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all v1 routes under /api/v1
app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """Top-level health check — confirms the app is running."""
    return {"status": "ok", "env": settings.APP_ENV}
