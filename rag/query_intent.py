import re
import logging
from dataclasses import dataclass, field
from openai import OpenAI
from rag.filters import Filters, DEFAULT_RADIUS_KM

log = logging.getLogger("culturai.query_intent")


GENRE_KEYWORDS = {
    "musique": "Music", "musical": "Music", "musicale": "Music", "concert": "Music",
    "rock": "Rock", "jazz": "Jazz", "rap": "Hip-Hop/Rap", "classique": "Classical",
    "electro": "Dance/Electronic", "pop": "Pop", "metal": "Metal",
    "chanson": "Chanson Francaise", "blues": "Blues", "reggae": "Reggae",
    "theatre": "Theatre", "théâtre": "Theatre",
    "danse": "Dance", "ballet": "Dance",
    "opera": "Opera", "opéra": "Opera",
    "comedie": "Comedy", "comédie": "Comedy", "humour": "Comedy", "humoriste": "Comedy",
    "cirque": "Circus & Specialty Acts", "magie": "Magic & Illusion",
    "sport": "Sports", "sportif": "Sports", "sportive": "Sports",
    "football": "Soccer", "foot": "Soccer", "rugby": "Rugby",
    "basket": "Basketball", "tennis": "Tennis", "handball": "Handball",
    "lutte": "Wrestling",
    "famille": "Family", "enfant": "Children's Theatre",
    "festival": "Fairs & Festivals",
}

_BUDGET_PATTERN = re.compile(
    r'(?:moins de|max|maximum|budget|pas plus de|sous les?)\s*(\d+)\s*(?:€|euros?|eur)?',
    re.IGNORECASE
)


@dataclass
class QueryIntent:
    city: str = ""
    genres: list = field(default_factory=list)
    budget_max: float = 0
    semantic_query: str = ""
    raw_query: str = ""

    @staticmethod
    def extract(query, city_coords, genre_keywords, api_key):
        """Extract intent from user query via heuristics + GPT reformulation."""
        log.info("--- Extraction d'intent ---")
        log.info("Requete brute : %s", query)

        intent = QueryIntent(raw_query=query)
        query_lower = query.lower()

        # A) Heuristic: city detection (longest match first to avoid partial matches)
        for city_key in sorted(city_coords.keys(), key=len, reverse=True):
            if city_key in query_lower:
                intent.city = city_key
                break

        # A) Heuristic: genre detection
        seen = set()
        for keyword, genre in genre_keywords.items():
            if keyword in query_lower and genre not in seen:
                intent.genres.append(genre)
                seen.add(genre)

        # A) Heuristic: budget detection
        match = _BUDGET_PATTERN.search(query)
        if match:
            intent.budget_max = float(match.group(1))

        log.info("Heuristique -> ville=%s, genres=%s, budget=%s",
                 intent.city or "(aucune)", intent.genres or "(aucun)", intent.budget_max or "(aucun)")

        # B) GPT semantic reformulation for FAISS
        system_msg = (
            "Reformule cette recherche d'evenements en mots-cles riches, "
            "dans le style d'une description d'evenement culturel. "
            "Extrais : type, style/ambiance, thematiques, ville, periode. "
            "Transforme les negations en positifs (\"pas classique\" -> \"contemporain, moderne\"). "
            "Reponds UNIQUEMENT la reformulation. Max 50 mots."
        )
        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": query},
        ]

        log.debug("GPT reformulation request",
                  extra={"json_data": {"model": "gpt-3.5-turbo", "messages": messages,
                                       "temperature": 0.3, "max_tokens": 100}})

        try:
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.3,
                max_tokens=100,
            )
            intent.semantic_query = response.choices[0].message.content.strip()

            log.debug("GPT reformulation response",
                      extra={"json_data": {
                          "semantic_query": intent.semantic_query,
                          "usage": {"prompt_tokens": response.usage.prompt_tokens,
                                    "completion_tokens": response.usage.completion_tokens,
                                    "total_tokens": response.usage.total_tokens}}})
        except Exception as e:
            log.error("GPT reformulation echouee : %s — fallback sur requete brute", e)
            intent.semantic_query = query

        log.info("Intent final",
                 extra={"json_data": {"city": intent.city, "genres": intent.genres,
                                      "budget_max": intent.budget_max,
                                      "semantic_query": intent.semantic_query,
                                      "raw_query": intent.raw_query}})
        return intent

    def to_filters(self):
        """Passe 1 : criteres heuristiques → filtres durs (query-only)."""
        return Filters(
            city=self.city,
            max_distance_km=DEFAULT_RADIUS_KM if self.city else 0,
            genres=list(self.genres),
            budget_max=self.budget_max)

    def to_filters_enriched(self, profile):
        """Passe 2b : fallback sur le profil pour les champs vides."""
        city = self.city or (profile.search_city if profile else "") or (profile.city if profile else "")
        genres = self.genres or (profile.preferred_genres if profile else [])
        budget = self.budget_max or (profile.budget_max if profile else 0)
        return Filters(
            city=city,
            max_distance_km=DEFAULT_RADIUS_KM if city else 0,
            genres=list(genres),
            budget_max=budget)


def diagnose_missing(intent):
    """Return a French string describing what's missing from the intent."""
    missing = []
    if not intent.city:
        missing.append("de ville")
    if not intent.genres:
        missing.append("de type d'evenement")
    if not missing:
        return ""
    return "Tu n'as pas precise " + " ni ".join(missing)
