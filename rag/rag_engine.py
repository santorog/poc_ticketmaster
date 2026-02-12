from rag.vector_store import VectorStore


class RagEngine:
    def __init__(self, vector_store: VectorStore, llm_client):
        self.vector_store = vector_store
        self.llm_client = llm_client

    def generate_response(self, user_query, profile=None):
        if profile:
            search_text = profile.to_search_text(user_query)
        else:
            search_text = user_query

        relevant_events = self.vector_store.query(search_text, top_k=10)
        return self.llm_client.generate_suggestion(user_query, relevant_events, profile=profile)
