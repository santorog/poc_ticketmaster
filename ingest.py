"""
Script d'ingestion : recupere tous les evenements musicaux en France
depuis Ticketmaster et les persiste dans le VectorStore (FAISS + JSON).

Usage:
    python ingest.py
    python ingest.py --max-pages 10   # limiter le nombre de pages
"""
import argparse
import config
from client.ticketmaster_client import TicketmasterClient
from rag.vector_store import VectorStore


def main():
    parser = argparse.ArgumentParser(description="Ingestion des evenements Ticketmaster")
    parser.add_argument("--max-pages", type=int, default=50,
                        help="Nombre max de pages a recuperer (defaut: 50, ~200 events/page)")
    parser.add_argument("--country", type=str, default="FR",
                        help="Code pays (defaut: FR)")
    parser.add_argument("--classification", type=str, default="music",
                        help="Classification (defaut: music)")
    args = parser.parse_args()

    print(f"Recuperation des evenements ({args.classification}, {args.country})...")
    client = TicketmasterClient(config.TICKETMASTER_API_KEY)
    client.DEFAULT_PAGE_SIZE = 200

    events = client.fetch_events(
        query="",
        country_code=args.country,
        classification_name=args.classification,
        max_pages=args.max_pages,
    )
    print(f"{len(events)} evenements recuperes.")

    if not events:
        print("Aucun evenement a indexer.")
        return

    print("Creation des embeddings et indexation...")
    vs = VectorStore(embedding_model="sentence-transformers/all-MiniLM-L6-v2")
    vs.add_events(events)

    vs.save()
    print(f"Sauvegarde terminee : {vs.count()} vecteurs dans db/")

    # Stats
    from collections import Counter
    genres = Counter(e.genre for e in events)
    cities = Counter(e.city for e in events)
    print(f"\nTop genres:")
    for g, c in genres.most_common(10):
        print(f"  {g or '(inconnu)'}: {c}")
    print(f"\nTop villes:")
    for v, c in cities.most_common(10):
        print(f"  {v or '(inconnue)'}: {c}")


if __name__ == "__main__":
    main()
