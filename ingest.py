"""
Ingestion complete des evenements Ticketmaster en France.

Recupere tous les segments (music, sports, arts, film, miscellaneous),
stocke dans SQLite, puis genere l'index FAISS.

Usage:
    python ingest.py                  # ingestion complete
    python ingest.py --embed-only     # re-generer FAISS depuis SQLite (sans fetch)
    python ingest.py --stats          # afficher les stats de la base
"""
import argparse
import time
import config
from client.ticketmaster_client import TicketmasterClient
from data.database import EventDatabase
from rag.vector_store import VectorStore

SEGMENTS = [
    "music",
    "sports",
    "arts",
    "film",
    "miscellaneous",
]


def fetch_all(db):
    client = TicketmasterClient(config.TICKETMASTER_API_KEY)
    total = 0

    for segment in SEGMENTS:
        print(f"\n--- {segment.upper()} ---")
        events = client.fetch_events(country_code="FR", classification_name=segment)
        db.upsert_events(events, classification=segment)
        print(f"  {len(events)} evenements recuperes")
        total += len(events)
        time.sleep(1)

    return total


def embed(db):
    events = db.get_all_events()
    if not events:
        print("Aucun evenement en base.")
        return

    print(f"\nCreation des embeddings pour {len(events)} evenements...")
    vs = VectorStore(embedding_model="sentence-transformers/all-MiniLM-L6-v2")
    vs.add_events(events)
    vs.save()
    print(f"Index FAISS sauvegarde : {vs.count()} vecteurs dans db/")


def print_stats(db):
    print(f"\nTotal : {db.count()} evenements")
    stats = db.stats()

    print("\nClassifications :")
    for cls, c in stats["classifications"]:
        print(f"  {cls or '(aucune)'}: {c}")

    print("\nTop genres :")
    for g, c in stats["genres"]:
        print(f"  {g or '(inconnu)'}: {c}")

    print("\nTop villes :")
    for v, c in stats["cities"]:
        print(f"  {v or '(inconnue)'}: {c}")


def main():
    parser = argparse.ArgumentParser(description="Ingestion des evenements Ticketmaster FR")
    parser.add_argument("--embed-only", action="store_true",
                        help="Re-generer FAISS depuis SQLite sans re-fetcher")
    parser.add_argument("--stats", action="store_true",
                        help="Afficher les stats de la base")
    args = parser.parse_args()

    db = EventDatabase()

    if args.stats:
        print_stats(db)
        db.close()
        return

    if not args.embed_only:
        print("Recuperation des evenements Ticketmaster FR...")
        total = fetch_all(db)
        print(f"\n{total} evenements recuperes au total.")

    print_stats(db)
    embed(db)
    db.close()
    print("\nIngestion terminee.")


if __name__ == "__main__":
    main()
