"""FastAPI application entry point.

PIPELINE FLOW:
  HTTP Request → FastAPI → API Router → POST /api/v1/emails/process
  → agent_graph.ainvoke(state)
  → ingest → classify → retrieve → draft → review → send | escalate
  → EmailResponse returned

UI PAGES (served as static HTML):
  GET /          → test email composer  (src/static/index.html)
  GET /inbox     → inbox / detail view  (src/static/inbox.html)

API DOCS:
  GET /docs      → Swagger UI
  GET /redoc     → ReDoc
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.core.config import settings
from src.core.logging import configure_logging
from src.api.v1.router import api_router

configure_logging()

_STATIC_DIR = Path(__file__).parent / "static"

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

# Serve static assets (CSS/JS if ever added)
app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")


@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    return {"status": "ok", "env": settings.APP_ENV}


@app.get("/", include_in_schema=False)
async def ui_index():
    return FileResponse(_STATIC_DIR / "index.html")


@app.get("/inbox", include_in_schema=False)
async def ui_inbox():
    return FileResponse(_STATIC_DIR / "inbox.html")
