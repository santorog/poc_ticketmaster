from rag.vector_store import VectorStore


class RagEngine:
    def __init__(self, vector_store: VectorStore, llm_client):
        self.vector_store = vector_store
        self.llm_client = llm_client

    def generate_response(self, user_query):
        relevant_events = self.vector_store.query(user_query)
        return self.llm_client.generate_suggestion(user_query, relevant_events)