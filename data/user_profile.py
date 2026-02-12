import os
import yaml
from dataclasses import dataclass, field
from openai import OpenAI


DEFAULT_PROFILE_PATH = "profiles/user.yaml"


@dataclass
class UserProfile:
    name: str = ""
    city: str = ""
    preferred_genres: list = field(default_factory=list)
    preferred_cities: list = field(default_factory=list)
    mood: str = ""
    openness: float = 0.5

    def save(self, path=DEFAULT_PROFILE_PATH):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        data = {
            "name": self.name,
            "city": self.city,
            "preferred_genres": self.preferred_genres,
            "preferred_cities": self.preferred_cities,
            "mood": self.mood,
            "openness": self.openness,
        }
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)

    @staticmethod
    def load(path=DEFAULT_PROFILE_PATH):
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return UserProfile(
            name=data.get("name", ""),
            city=data.get("city", ""),
            preferred_genres=data.get("preferred_genres", []),
            preferred_cities=data.get("preferred_cities", []),
            mood=data.get("mood", ""),
            openness=float(data.get("openness", 0.5)),
        )

    @staticmethod
    def exists(path=DEFAULT_PROFILE_PATH):
        return os.path.exists(path)

    @staticmethod
    def from_transcription(text, api_key):
        """Use GPT to extract a structured profile from free-form voice text."""
        client = OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": (
                "Analyse cette presentation d'un utilisateur et extrais un profil structure.\n\n"
                f"Texte : \"{text}\"\n\n"
                "Reponds UNIQUEMENT en YAML valide (sans balises markdown) avec ces champs :\n"
                "- name: son prenom (ou \"\" si non mentionne)\n"
                "- city: sa ville principale (ou \"\" si non mentionnee)\n"
                "- preferred_genres: liste de genres/styles qu'il aime (musique, theatre, sport, etc.)\n"
                "- preferred_cities: liste de villes qu'il frequente (ou [])\n"
                "- mood: son humeur ou envie du moment (ou \"\")\n"
                "- openness: de 0.0 (veut uniquement ses gouts) a 1.0 (tres ouvert a la decouverte), "
                "estime selon ce qu'il dit\n"
            )}],
            temperature=0.3,
            max_tokens=500,
        )

        yaml_text = response.choices[0].message.content.strip()
        data = yaml.safe_load(yaml_text)

        return UserProfile(
            name=data.get("name", ""),
            city=data.get("city", ""),
            preferred_genres=data.get("preferred_genres", []),
            preferred_cities=data.get("preferred_cities", []),
            mood=data.get("mood", ""),
            openness=float(data.get("openness", 0.5)),
        )

    def to_prompt_context(self):
        lines = []
        if self.name:
            lines.append(f"Prenom : {self.name}")
        if self.city:
            lines.append(f"Ville : {self.city}")
        if self.preferred_genres:
            lines.append(f"Adore : {', '.join(self.preferred_genres)}")
        if self.preferred_cities:
            lines.append(f"Villes preferees : {', '.join(self.preferred_cities)}")
        if self.mood:
            lines.append(f"Humeur du moment : {self.mood}")
        lines.append(f"Ouverture a la decouverte : {self.openness:.1f}/1.0")
        return "\n".join(lines)

    def to_search_text(self, query):
        """Enrich query with profile preferences for better FAISS recall."""
        parts = [query]
        if self.preferred_genres:
            parts.append(" ".join(self.preferred_genres))
        if self.city:
            parts.append(self.city)
        return " ".join(parts)
