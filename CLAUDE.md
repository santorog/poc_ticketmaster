# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

POC for an AI-powered event recommendation engine (CulturAI). Fetches events from Ticketmaster Discovery v2 API, stores them in SQLite, indexes them with FAISS vector embeddings, and uses GPT to generate personalized recommendations via RAG. Supports voice input (Whisper) and text input. User profiles are created via voice and persisted as YAML. Recommendations are prioritized by distance, genre, date, price, and quality. User-facing text is in French.

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

# Run integration tests (requires TICKETMASTER_CONSUMER_KEY in .env)
python -m pytest tests/ticketmaster_it.py -v
```

## Environment Variables

Requires a `.env` file with:
- `TICKETMASTER_CONSUMER_KEY` — Ticketmaster Discovery API consumer key
- `OPENAI_API_KEY` — OpenAI API key (used for GPT recommendations, Whisper transcription, profile extraction)

## Architecture

The app follows a two-phase pipeline:

### Phase 1 — Ingestion (`ingest.py`)
```
Ticketmaster API → TicketmasterClient (fetch by genre per segment) → SQLite (source of truth) → VectorStore (embed + persist FAISS)
```
- Small segments (sports, film) are fetched by segment name (fit within 1200 paging limit)
- Large segments (music, arts, miscellaneous) are fetched by individual genre ID to bypass the 1200 limit
- SQLite dedup handles overlapping results
- Events store venue coordinates (latitude/longitude) for distance calculations

### Phase 2 — Query (`app.py`)
```
1. Voice/Text → profile creation (GPT extracts structured YAML) → saved to profiles/user.yaml
2. Voice/Text → user query → FAISS search (enriched with profile) → distance computation → GPT recommendation
```

### User Profile (`profiles/user.yaml`)
- Created via voice or text, extracted by GPT into structured YAML
- Fields: `name`, `city`, `preferred_genres`, `preferred_cities`, `mood`, `openness`, `search_city`, `search_dates`, `budget_max`
- Persisted locally, loaded automatically on next launch
- `search_city` used for distance calculations, `preferred_genres` enrich FAISS query

### Recommendation Criteria (priority order)
1. **Distance** — events near the user's `search_city` (Haversine from venue lat/lon)
2. **Genre** — match with user's `preferred_genres`
3. **Date** — match with user's `search_dates`
4. **Price** — within `budget_max` (when available from API)
5. **Quality** — richness of event, semantic match, venue

### Files

- **`ingest.py`** — Bulk ingestion: fetches all Ticketmaster genres across 5 segments for France, stores in SQLite, generates FAISS index
- **`app.py`** — Interactive CLI: two-step voice/text flow (profile + query), loads FAISS, generates recommendations
- **`data/user_profile.py`** — `UserProfile` dataclass: YAML save/load, GPT extraction from voice transcription, search context (city, dates, budget)
- **`data/event.py`** — `Event` dataclass (id, name, description, date, url, venue, city, genre, price, latitude, longitude) with `to_text()` for embeddings
- **`data/database.py`** — SQLite `EventDatabase`: upsert with dedup, auto-migration for new columns, query by classification, stats
- **`geo/distance.py`** — Haversine distance calculation, 50+ French city coordinates lookup
- **`voice/recorder.py`** — Records audio from microphone using sounddevice, saves to temp WAV file
- **`voice/transcriber.py`** — Transcribes audio via OpenAI Whisper API (`whisper-1`, language=fr)
- **`client/ticketmaster_client.py`** — Ticketmaster Discovery v2 client; pagination, rate limiting (0.25s), genre fallback, parses venue coordinates and price
- **`client/eventbrite_client.py`** — Legacy Eventbrite client (kept as reference, no longer used)
- **`data/event_repository.py`** — Repository abstraction, delegates to TicketmasterClient
- **`rag/vector_store.py`** — FAISS-based vector store with `save()`/`load()` persistence to `db/` directory
- **`rag/rag_engine.py`** — RAG orchestration: enriches query with profile, computes distances, passes to LLM
- **`llm/llm_client.py`** — OpenAI GPT integration; system prompt as enthusiastic culture advisor, prioritized criteria, distance-aware, includes booking links
- **`config.py`** — Loads `.env` and exposes API keys

### Persistence

- `db/events.db` — SQLite database (source of truth, gitignored)
- `db/faiss.index` — FAISS vector index (gitignored)
- `db/events.json` — Event data mapped to FAISS index positions (gitignored)
- `profiles/user.yaml` — User profile (gitignored)

## Key Dependencies

- `openai` — LLM recommendations + Whisper transcription + profile extraction
- `requests` — Ticketmaster HTTP client
- `faiss-cpu` + `sentence-transformers` — Local vector embeddings and similarity search (model: `paraphrase-multilingual-MiniLM-L12-v2`)
- `sounddevice` + `soundfile` — Microphone recording for voice input
- `pyyaml` — User profile persistence
- `python-dotenv` — Environment variable loading
- `sqlite3` — Event storage (Python stdlib)

## Ticketmaster API Notes

- Auth: query param `apikey` (consumer key), no OAuth needed
- `locale=*` required for FR events (locale=fr-fr returns 0 results)
- `startDateTime`/`endDateTime` filters are incompatible with FR source — omitted
- `classificationName` + `keyword` combined returns 0 for FR — use one or the other
- Deep paging limit: `page × size` must be < 1200 (6 pages × 200) — bypassed by querying per genre ID
- Events have a `description` field (rich French text) checked first, then `info`, then synthesized from genre + venue + city
- Venue coordinates (`latitude`/`longitude`) available for ~78% of FR events
- `priceRanges` not available on free tier (neither FR nor US) — price field ready but unpopulated
- Rate limit: 5 req/s, 5000 req/day on free tier; client uses 0.25s delay (4 req/s)

## Conventions

- Constructor-based dependency injection across components
- French language for all user-facing strings and LLM prompts
- TicketmasterClient uses class-level constants for API configuration
- `@dataclass` for domain models
- SQLite as source of truth, FAISS as derived index (can be regenerated via `--embed-only`)
- Database auto-migration for schema changes (new columns added without data loss)
