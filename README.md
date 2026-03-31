# Customer Support Email Agent

A production-grade AI-powered customer support email agent built with **LangGraph**, **LangChain**, **FastAPI**, and **OpenAI**.

## Overview

This agent automatically processes incoming customer support emails, classifies intent, retrieves relevant knowledge, and drafts contextual responses using a multi-node LangGraph workflow.

## Tech Stack

| Layer | Technology |
|---|---|
| Python | 3.12 |
| Package Manager | uv |
| API Framework | FastAPI |
| Agent Orchestration | LangGraph |
| LLM Chains | LangChain |
| LLM Provider | OpenAI (GPT-4o) |
| Data Validation | Pydantic v2 |

## Project Structure

```
customer-support-email-agent/
├── src/
│   ├── api/               # FastAPI routers and endpoints
│   ├── graph/             # LangGraph workflow definitions
│   ├── nodes/             # Individual LangGraph node implementations
│   ├── services/          # Business logic and external service clients
│   ├── schemas/           # Pydantic request/response models
│   ├── core/              # App config, settings, logging
│   ├── utils/             # Shared helpers and utilities
│   ├── knowledge_base/    # Static knowledge / FAQ documents
│   └── main.py            # FastAPI app entry point
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```

## Getting Started

### Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/) (manages Python 3.12 and all dependencies)
- An OpenAI API key

### Installation

```bash
# Clone the repo
git clone https://github.com/jndumu/customer-support-email-agent.git
cd customer-support-email-agent

# Create virtual environment
uv venv .venv

# Activate the virtual environment
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows (Command Prompt)
# .venv\Scripts\Activate.ps1     # Windows (PowerShell)

# Install all dependencies
uv sync

# Install dev dependencies too
uv sync --extra dev

# Configure environment
cp .env.example .env
# Edit .env and set your OPENAI_API_KEY
```

### Running the API

```bash
uv run uvicorn src.main:app --reload
```

Visit `http://localhost:8000/docs` for the interactive API documentation.

### Running Tests

```bash
uv run pytest tests/ -v --cov=src
```

## Agent Workflow

```
Ingest Email
    │
    ▼
Classify Intent
    │
    ▼
Retrieve Knowledge
    │
    ▼
Draft Response
    │
    ▼
Review / Escalate
    │
    ▼
Send Response
```

## Environment Variables

See `.env.example` for all required and optional configuration values.

## License

MIT
