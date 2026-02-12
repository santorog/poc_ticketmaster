"""
Ingestion complete des evenements Ticketmaster en France.

Recupere tous les segments par genre (pour depasser la limite de 1200
evenements par requete), stocke dans SQLite, puis genere l'index FAISS.

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

# Segments with few events in FR — fetch by segment name (fits in 1200)
SMALL_SEGMENTS = [
    "sports",
    "film",
]

# Segments with many events — fetch by individual genre ID to get full coverage
# (segment_name, genre_id, genre_label)
GENRE_QUERIES = [
    # Music (24 genres)
    ("music", "KnvZfZ7vAvv", "Alternative"),
    ("music", "KnvZfZ7vAve", "Ballads/Romantic"),
    ("music", "KnvZfZ7vAvd", "Blues"),
    ("music", "KnvZfZ7vAvA", "Chanson Francaise"),
    ("music", "KnvZfZ7vAvk", "Children's Music"),
    ("music", "KnvZfZ7vAeJ", "Classical"),
    ("music", "KnvZfZ7vAv6", "Country"),
    ("music", "KnvZfZ7vAvF", "Dance/Electronic"),
    ("music", "KnvZfZ7vAva", "Folk"),
    ("music", "KnvZfZ7vAv1", "Hip-Hop/Rap"),
    ("music", "KnvZfZ7vAvJ", "Holiday"),
    ("music", "KnvZfZ7vAvE", "Jazz"),
    ("music", "KnvZfZ7vAJ6", "Latin"),
    ("music", "KnvZfZ7vAvI", "Medieval/Renaissance"),
    ("music", "KnvZfZ7vAvt", "Metal"),
    ("music", "KnvZfZ7vAvn", "New Age"),
    ("music", "KnvZfZ7vAvl", "Other"),
    ("music", "KnvZfZ7vAev", "Pop"),
    ("music", "KnvZfZ7vAee", "R&B"),
    ("music", "KnvZfZ7vAed", "Reggae"),
    ("music", "KnvZfZ7vAe7", "Religious"),
    ("music", "KnvZfZ7vAeA", "Rock"),
    ("music", "KnvZfZ7vAe6", "Undefined"),
    ("music", "KnvZfZ7vAeF", "World"),
    # Arts & Theatre (20 genres)
    ("arts", "KnvZfZ7v7na", "Children's Theatre"),
    ("arts", "KnvZfZ7v7n1", "Circus & Specialty Acts"),
    ("arts", "KnvZfZ7v7nJ", "Classical"),
    ("arts", "KnvZfZ7vAe1", "Comedy"),
    ("arts", "KnvZfZ7v7nE", "Cultural"),
    ("arts", "KnvZfZ7v7nI", "Dance"),
    ("arts", "KnvZfZ7v7nt", "Espectaculo"),
    ("arts", "KnvZfZ7v7nn", "Fashion"),
    ("arts", "KnvZfZ7v7nl", "Fine Art"),
    ("arts", "KnvZfZ7v7lv", "Magic & Illusion"),
    ("arts", "KnvZfZ7v7le", "Miscellaneous"),
    ("arts", "KnvZfZ7v7ld", "Miscellaneous Theatre"),
    ("arts", "KnvZfZ7v7l7", "Multimedia"),
    ("arts", "KnvZfZ7v7lA", "Music"),
    ("arts", "KnvZfZ7v7lk", "Opera"),
    ("arts", "KnvZfZ7v7l6", "Performance Art"),
    ("arts", "KnvZfZ7v7lF", "Puppetry"),
    ("arts", "KnvZfZ7v7la", "Spectacular"),
    ("arts", "KnvZfZ7v7l1", "Theatre"),
    ("arts", "KnvZfZ7v7lJ", "Variety"),
    # Miscellaneous (16 genres)
    ("miscellaneous", "KnvZfZ7vAAa", "Casino/Gaming"),
    ("miscellaneous", "KnvZfZ7vAA1", "Comedy"),
    ("miscellaneous", "KnvZfZ7vAAE", "Community/Civic"),
    ("miscellaneous", "KnvZfZ7v7lE", "Community/Cultural"),
    ("miscellaneous", "KnvZfZ7vAeE", "Fairs & Festivals"),
    ("miscellaneous", "KnvZfZ7vA1n", "Family"),
    ("miscellaneous", "KnvZfZ7vAAI", "Food & Drink"),
    ("miscellaneous", "KnvZfZ7vAAl", "Health/Wellness"),
    ("miscellaneous", "KnvZfZ7vAAJ", "Hobby/Special Interest Expos"),
    ("miscellaneous", "KnvZfZ7vAAt", "Holiday"),
    ("miscellaneous", "KnvZfZ7v7lI", "Ice Shows"),
    ("miscellaneous", "KnvZfZ7vAJe", "Lecture/Seminar"),
    ("miscellaneous", "KnvZfZ7vAAF", "Multimedia"),
    ("miscellaneous", "KnvZfZ7vAAn", "Psychics/Mediums/Hypnotists"),
    ("miscellaneous", "KnvZfZ7v7lt", "Special Interest/Hobby"),
    ("miscellaneous", "KnvZfZ7v7ll", "Undefined"),
]


def fetch_all(db):
    client = TicketmasterClient(config.TICKETMASTER_API_KEY)
    total = 0

    # Small segments: fetch by segment name (fits in 1200)
    for segment in SMALL_SEGMENTS:
        print(f"\n--- {segment.upper()} ---")
        events = client.fetch_events(country_code="FR", classification_name=segment)
        db.upsert_events(events, classification=segment)
        print(f"  {len(events)} evenements")
        total += len(events)
        time.sleep(1)

    # Large segments: fetch by individual genre for full coverage
    current_segment = None
    for segment, genre_id, genre_label in GENRE_QUERIES:
        if segment != current_segment:
            current_segment = segment
            print(f"\n--- {segment.upper()} (par genre) ---")

        events = client.fetch_events(country_code="FR", genre_id=genre_id)
        if events:
            db.upsert_events(events, classification=segment)
            print(f"  {genre_label}: {len(events)} evenements")
            total += len(events)
        time.sleep(0.5)

    return total


def embed(db):
    events = db.get_all_events()
    if not events:
        print("Aucun evenement en base.")
        return

    print(f"\nCreation des embeddings pour {len(events)} evenements...")
    vs = VectorStore(embedding_model="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
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
        print(f"\n{total} evenements recuperes au total (avant dedup).")

    print_stats(db)
    embed(db)
    db.close()
    print("\nIngestion terminee.")


if __name__ == "__main__":
    main()
