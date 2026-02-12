from rag.vector_store import VectorStore
from geo.distance import compute_distance


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

        # Compute distances from user's search city
        distances = {}
        search_city = profile.search_city if profile else None
        if not search_city and profile:
            search_city = profile.city
        if search_city:
            for e in relevant_events:
                d = compute_distance(search_city, e)
                if d is not None:
                    distances[e.id] = d

        return self.llm_client.generate_suggestion(
            user_query, relevant_events, profile=profile, distances=distances
        )
