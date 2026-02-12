# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

POC for an AI-powered event recommendation engine (CulturAI). Fetches events from Ticketmaster Discovery v2 API, stores them in SQLite, indexes them with FAISS vector embeddings, and uses GPT to generate personalized recommendations via RAG. User-facing text is in French. Recommendations include Ticketmaster affiliate booking links.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Ingest all FR events into SQLite + FAISS
python ingest.py

# Re-generate FAISS index from SQLite (no API fetch)
python ingest.py --embed-only

# Show database stats
python ingest.py --stats

# Run the application (interactive CLI, requires prior ingestion)
python app.py

# Run with a user profile for personalized recommendations
python app.py --profile profiles/default.yaml

# Run integration tests (requires TICKETMASTER_CONSUMER_KEY in .env)
python -m pytest tests/ticketmaster_it.py -v
```

## Environment Variables

Requires a `.env` file with:
- `TICKETMASTER_CONSUMER_KEY` — Ticketmaster Discovery API consumer key
- `OPENAI_API_KEY` — OpenAI API key

## Architecture

The app follows a two-phase pipeline:

### Phase 1 — Ingestion (`ingest.py`)
```
Ticketmaster API → TicketmasterClient (fetch by segment) → SQLite (source of truth) → VectorStore (embed + persist FAISS)
```

### Phase 2 — Query (`app.py`)
```
User Query + UserProfile (optional) → VectorStore.load() → enriched semantic search (FAISS) → RagEngine → LLMClient (GPT personalized recommendation with booking links) → Output
```

### User Profiles (`profiles/`)
- YAML files defining user preferences: `name`, `city`, `preferred_genres`, `preferred_cities`, `openness` (0.0–1.0)
- `openness` controls the discovery/familiarity balance:
  - 0.0 = strict (top_k=5, query heavily enriched with preferences, LLM told to stay in comfort zone)
  - 0.5 = balanced (top_k=10, light enrichment, LLM suggests 1 discovery)
  - 1.0 = explorer (top_k=15, raw query, LLM maximizes diversity)
- Profile enriches both FAISS search (via `to_search_text()`) and LLM prompt (via `to_prompt_context()`)

### Files

- **`ingest.py`** — Bulk ingestion script: fetches all 5 Ticketmaster segments (music, sports, arts, film, miscellaneous) for France, stores in SQLite, generates FAISS index
- **`app.py`** — Interactive CLI: loads persisted FAISS index, optionally loads user profile (`--profile`), performs semantic search, generates GPT recommendations
- **`data/user_profile.py`** — `UserProfile` dataclass with YAML loading, `to_search_text()` for FAISS enrichment, `to_prompt_context()` for LLM, `compute_top_k()` based on openness
- **`profiles/default.yaml`** — Example user profile (Santiago, Paris, Rock/Jazz/Chanson Francaise, openness 0.7)
- **`client/ticketmaster_client.py`** — Ticketmaster Discovery v2 client; pagination (max page 5 × 200 = 1200 per query), rate limiting (0.25s delay), genre fallback from subGenre/segment
- **`client/eventbrite_client.py`** — Legacy Eventbrite client (kept as reference, no longer used)
- **`data/event.py`** — `Event` dataclass (id, name, description, date, url, venue, city, genre) with `to_text()` for embeddings
- **`data/database.py`** — SQLite `EventDatabase`: upsert with dedup on event ID, query by classification, stats
- **`data/event_repository.py`** — Repository abstraction, delegates to TicketmasterClient
- **`rag/vector_store.py`** — FAISS-based vector store with `save()`/`load()` persistence to `db/` directory
- **`rag/rag_engine.py`** — RAG orchestration: enriches query with profile, retrieves top-K similar events from VectorStore, passes profile to LLM
- **`llm/llm_client.py`** — OpenAI GPT integration; French-language prompts, profile-aware instructions (openness-based), includes Ticketmaster booking links
- **`config.py`** — Loads `.env` and exposes API keys

### Persistence (`db/` directory, gitignored)

- `events.db` — SQLite database (source of truth)
- `faiss.index` — FAISS vector index
- `events.json` — Event data mapped to FAISS index positions

## Key Dependencies

- `openai` — LLM recommendation generation
- `requests` — Ticketmaster HTTP client
- `faiss-cpu` + `sentence-transformers` — Local vector embeddings and similarity search
- `python-dotenv` — Environment variable loading
- `pyyaml` — User profile loading
- `sqlite3` — Event storage (Python stdlib)

## Ticketmaster API Notes

- Auth: query param `apikey` (consumer key), no OAuth needed
- `locale=*` required for FR events (locale=fr-fr returns 0 results)
- `startDateTime`/`endDateTime` filters are incompatible with FR source — omitted
- `classificationName` + `keyword` combined returns 0 for FR — use one or the other
- Deep paging limit: `page × size` must be < 1200 (6 pages × 200)
- FR events rarely have `info` field; description is synthesized from genre + venue + city
- Rate limit: 5 req/s, 5000 req/day on free tier

## Conventions

- Constructor-based dependency injection across components
- French language for all user-facing strings and LLM prompts
- TicketmasterClient uses class-level constants for API configuration
- `@dataclass` for domain models
- SQLite as source of truth, FAISS as derived index (can be regenerated via `--embed-only`)
