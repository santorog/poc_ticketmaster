import logging
from rag.vector_store import VectorStore
from rag.filters import apply_filters, evaluate_results, MAX_EVENTS
from rag.query_intent import QueryIntent, GENRE_KEYWORDS
from geo.distance import CITY_COORDS

log = logging.getLogger("culturai.rag_engine")


class RagEngine:
    def __init__(self, vector_store: VectorStore, llm_client, api_key):
        self.vector_store = vector_store
        self.llm_client = llm_client
        self.api_key = api_key

    def search(self, intent, filters):
        """Filter-then-rank: apply hard filters, then FAISS semantic ranking."""
        search_text = intent.semantic_query or intent.raw_query
        log.info("=== search() ===")
        log.info("Texte FAISS : %s", search_text)
        log.info("Filtres : %s", filters.describe())

        if filters.is_empty:
            log.info("Pas de filtres → recherche FAISS standard")
            ranked = self.vector_store.query(search_text, top_k=MAX_EVENTS)
            return ranked, {}

        eligible_indices, distances_km = apply_filters(self.vector_store.event_map, filters)

        if not eligible_indices:
            log.info("Aucun evenement eligible apres filtrage")
            return [], distances_km

        ranked = self.vector_store.query_filtered(search_text, eligible_indices, top_k=MAX_EVENTS)
        return ranked, distances_km

    def generate_response(self, user_query, profile=None):
        """Pass 1: query-only. Returns (response, is_good, intent)."""
        log.info("========== PASSE 1 : query-only ==========")
        intent = QueryIntent.extract(user_query, CITY_COORDS, GENRE_KEYWORDS, self.api_key)

        filters = intent.to_filters()
        log.info("Filtres passe 1 : %s (profil NON utilise)", filters.describe())

        ranked_events, distances_km = self.search(intent, filters)

        is_good = evaluate_results(len(ranked_events))
        log.info("Passe 1 terminee : is_good=%s, count=%d", is_good, len(ranked_events))

        if not ranked_events:
            log.info("Passe 1 : aucun resultat")
            return None, False, intent

        log.info("Appel LLM pour generation de recommandations...")
        response = self.llm_client.generate_suggestion(
            user_query, ranked_events, profile=profile, distances=distances_km)
        return response, is_good, intent

    def generate_enriched_response(self, user_query, profile, original_intent):
        """Pass 2b: enrich intent with profile as fallback."""
        log.info("========== PASSE 2b : enrichissement profil ==========")

        filters = original_intent.to_filters_enriched(profile)
        log.info("Filtres enrichis : %s", filters.describe())

        ranked_events, distances_km = self.search(original_intent, filters)

        if not ranked_events:
            log.info("Passe 2b : aucun resultat")
            return None

        log.info("Appel LLM pour generation de recommandations (enrichi)...")
        return self.llm_client.generate_suggestion(
            user_query, ranked_events, profile=profile, distances=distances_km)

    def generate_refined_response(self, original_query, refinement, profile=None):
        """Pass 2a: user refined their search."""
        combined_query = f"{original_query}. {refinement}"
        log.info("========== PASSE 2a : precision utilisateur ==========")
        log.info("Requete combinee : %s", combined_query)

        intent = QueryIntent.extract(combined_query, CITY_COORDS, GENRE_KEYWORDS, self.api_key)

        filters = intent.to_filters_enriched(profile) if profile else intent.to_filters()
        log.info("Filtres passe 2a : %s", filters.describe())

        ranked_events, distances_km = self.search(intent, filters)

        if not ranked_events:
            log.info("Passe 2a : aucun resultat")
            return None

        log.info("Appel LLM pour generation de recommandations (affine)...")
        return self.llm_client.generate_suggestion(
            combined_query, ranked_events, profile=profile, distances=distances_km)
