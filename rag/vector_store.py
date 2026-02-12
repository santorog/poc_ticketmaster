import os
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from data.event import Event


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

    def query(self, user_query: str, top_k=5):
        query_vec = self.embedding_model.encode([user_query])
        distances, indices = self.index.search(np.array(query_vec).astype("float32"), top_k)

        return [self.event_map[i] for i in indices[0] if i in self.event_map]

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
