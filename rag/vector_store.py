import os
import json
import logging
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from data.event import Event

log = logging.getLogger("culturai.vector_store")


class VectorStore:
    DEFAULT_DIR = "db"
    INDEX_FILE = "faiss.index"
    EVENTS_FILE = "events.json"

    def __init__(self, embedding_model="all-MiniLM-L6-v2", persist_dir=DEFAULT_DIR):
        self.embedding_model = SentenceTransformer(embedding_model)
        self.persist_dir = persist_dir
        self.index = None
        self.event_map = {}

    def init_db(self):
        dim = self.embedding_model.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatL2(dim)
        return self.index

    def add_events(self, events: [Event]):
        if not events:
            return

        if self.index is None:
            self.init_db()

        texts = [e.to_text() for e in events]
        vectors = self.embedding_model.encode(texts)

        self.index.add(np.array(vectors).astype("float32"))

        for event in events:
            self.event_map[len(self.event_map)] = event

    def query(self, user_query: str, top_k=50):
        log.info("--- Recherche FAISS ---")
        log.info("Texte de recherche : %s", user_query)
        log.info("top_k=%d, index_size=%d", top_k, self.count())

        query_vec = self.embedding_model.encode([user_query])
        distances, indices = self.index.search(np.array(query_vec).astype("float32"), top_k)

        results = [
            (self.event_map[i], float(distances[0][rank]))
            for rank, i in enumerate(indices[0])
            if i in self.event_map
        ]

        log.info("FAISS a retourne %d candidats", len(results))
        if results:
            log.debug("Top 10 candidats FAISS (avant scoring)",
                      extra={"json_data": [
                          {"rank": r + 1, "id": e.id, "name": e.name,
                           "genre": e.genre, "city": e.city,
                           "l2_distance": round(d, 4)}
                          for r, (e, d) in enumerate(results[:10])]})

        return results

    def query_filtered(self, user_query, eligible_indices, top_k=20):
        """FAISS search restricted to a pre-filtered subset of indices."""
        log.info("--- Recherche FAISS filtree ---")
        log.info("Texte de recherche : %s", user_query)
        log.info("Candidats eligibles : %d, top_k=%d", len(eligible_indices), top_k)

        query_vec = self.embedding_model.encode([user_query]).astype("float32")
        vectors = np.array([self.index.reconstruct(i) for i in eligible_indices], dtype="float32")
        l2_distances = np.sum((vectors - query_vec) ** 2, axis=1)
        ranked_order = np.argsort(l2_distances)[:top_k]

        results = [
            (self.event_map[eligible_indices[rank]], float(l2_distances[rank]))
            for rank in ranked_order
        ]

        log.info("FAISS filtre a retourne %d resultats", len(results))
        if results:
            log.debug("Top 10 resultats FAISS filtres",
                      extra={"json_data": [
                          {"rank": r + 1, "id": e.id, "name": e.name,
                           "genre": e.genre, "city": e.city,
                           "l2_distance": round(d, 4)}
                          for r, (e, d) in enumerate(results[:10])]})

        return results

    def save(self):
        os.makedirs(self.persist_dir, exist_ok=True)

        faiss.write_index(self.index, os.path.join(self.persist_dir, self.INDEX_FILE))

        events_data = []
        for idx in sorted(self.event_map.keys()):
            e = self.event_map[idx]
            events_data.append({
                "id": e.id, "name": e.name, "description": e.description,
                "date": e.date, "url": e.url, "venue": e.venue,
                "city": e.city, "genre": e.genre, "price": e.price,
                "latitude": e.latitude, "longitude": e.longitude,
            })

        with open(os.path.join(self.persist_dir, self.EVENTS_FILE), "w", encoding="utf-8") as f:
            json.dump(events_data, f, ensure_ascii=False, indent=2)

    def load(self):
        index_path = os.path.join(self.persist_dir, self.INDEX_FILE)
        events_path = os.path.join(self.persist_dir, self.EVENTS_FILE)

        if not os.path.exists(index_path) or not os.path.exists(events_path):
            return False

        self.index = faiss.read_index(index_path)

        with open(events_path, "r", encoding="utf-8") as f:
            events_data = json.load(f)

        self.event_map = {}
        for i, ed in enumerate(events_data):
            self.event_map[i] = Event(**ed)

        return True

    def count(self):
        return self.index.ntotal if self.index else 0
