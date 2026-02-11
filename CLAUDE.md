# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

POC for an AI-powered event recommendation engine (CulturAI). Searches Eventbrite for events, indexes them with vector embeddings, and uses GPT to generate personalized recommendations via RAG. User-facing text is in French.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application (interactive CLI)
python app.py

# Run integration tests (requires EVENTBRITE_PRIVATE_TOKEN in .env)
python -m pytest tests/eventbrite_it.py -v
```

## Environment Variables

Requires a `.env` file with:
- `EVENTBRITE_TOKEN` — Eventbrite API token
- `OPENAI_API_KEY` — OpenAI API key
- `EVENTBRITE_PRIVATE_TOKEN` — used by integration tests

## Architecture

The app follows a layered pipeline:

```
User Query → EventbriteClient (fetch) → VectorStore (embed + index) → RagEngine (retrieve) → LLMClient (recommend) → Output
```

- **`app.py`** — Entry point, orchestrates the pipeline
- **`client/eventbrite_client.py`** — Eventbrite API v3 client; handles pagination, date range filtering, response parsing into Event objects
- **`data/event.py`** — `Event` dataclass (id, name, description, date, url)
- **`data/event_repository.py`** — Repository abstraction (currently stubbed)
- **`rag/vector_store.py`** — FAISS-based vector store using `sentence-transformers` (all-MiniLM-L6-v2) for local embeddings
- **`rag/rag_engine.py`** — RAG orchestration: retrieves top-K similar events from VectorStore
- **`llm/llm_client.py`** — OpenAI GPT integration; builds French-language prompts and generates recommendations
- **`config.py`** — Loads `.env` and exposes API keys

## Key Dependencies

- `openai` — LLM recommendation generation
- `requests` — Eventbrite HTTP client
- `faiss-cpu` + `sentence-transformers` — Local vector embeddings and similarity search
- `langchain` — LLM orchestration
- `python-dotenv` — Environment variable loading

## Conventions

- Constructor-based dependency injection across components
- French language for all user-facing strings and LLM prompts
- EventbriteClient uses class-level constants for API configuration (BASE_URL, SEARCH_ENDPOINT, etc.)
- `@dataclass` for domain models
