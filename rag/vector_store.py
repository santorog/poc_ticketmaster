import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from data.event import Event

# Todo: text-embedding-3-small from Open AI to keep json structure

class VectorStore:
    def __init__(self, embedding_model="all-MiniLM-L6-v2"):
        self.embedding_model = SentenceTransformer(embedding_model)
        self.index = None
        self.event_map = {}

    def init_db(self):
        dim = self.embedding_model.get_sentence_embedding_dimension()
        self.index = faiss.IndexFlatL2(dim)
        return self.index

    def add_events(self, events: [Event]):
        texts = [f"{e.name}. {e.description}" for e in events]
        vectors = self.embedding_model.encode(texts)

        self.db.add(np.array(vectors).astype("float32"))

        for i, event in enumerate(events):
            self.event_map[len(self.event_map)] = event  # index -> event

    def query(self, user_query: str, top_k=5):
        query_vec = self.embedding_model.encode([user_query])
        distances, indices = self.db.search(np.array(query_vec).astype("float32"), top_k)

        return [self.event_map[i] for i in indices[0] if i in self.event_map]