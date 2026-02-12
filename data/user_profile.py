from dataclasses import dataclass, field
import yaml


@dataclass
class UserProfile:
    name: str = ""
    city: str = ""
    preferred_genres: list = field(default_factory=list)
    preferred_cities: list = field(default_factory=list)
    openness: float = 0.5

    @staticmethod
    def load(path):
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return UserProfile(
            name=data.get("name", ""),
            city=data.get("city", ""),
            preferred_genres=data.get("preferred_genres", []),
            preferred_cities=data.get("preferred_cities", []),
            openness=float(data.get("openness", 0.5)),
        )

    def to_search_text(self, query):
        """Enrich the user query with profile preferences for FAISS search.

        At openness=0, heavily biases toward preferred genres/cities.
        At openness=1, returns the raw query unchanged.
        """
        if self.openness >= 1.0:
            return query

        parts = [query]
        if self.preferred_genres:
            parts.append(" ".join(self.preferred_genres))
        if self.preferred_cities:
            parts.append(" ".join(self.preferred_cities))
        elif self.city:
            parts.append(self.city)

        return " ".join(parts)

    def to_prompt_context(self):
        lines = [f"Nom : {self.name}"]
        if self.city:
            lines.append(f"Ville : {self.city}")
        if self.preferred_genres:
            lines.append(f"Genres preferes : {', '.join(self.preferred_genres)}")
        if self.preferred_cities:
            lines.append(f"Villes preferees : {', '.join(self.preferred_cities)}")
        lines.append(f"Ouverture a la decouverte : {self.openness:.1f}/1.0")
        return "\n".join(lines)

    def compute_top_k(self):
        """Return top_k based on openness: 5 at 0.0, 15 at 1.0."""
        return int(5 + self.openness * 10)
