from openai import OpenAI
from data.event import Event


class LLMClient:
    def __init__(self, api_key, model="gpt-3.5-turbo"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def generate_suggestion(self, query, events: [Event], profile=None):
        prompt = self._build_prompt(query, events, profile)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1000
        )

        return response.choices[0].message.content.strip()

    def _build_prompt(self, query, events: [Event], profile=None):
        event_details = "\n\n".join([
            f"Titre : {e.name}\n"
            f"Genre : {e.genre}\n"
            f"Lieu : {e.venue}\n"
            f"Ville : {e.city}\n"
            f"Date : {e.date}\n"
            f"Description : {e.description}\n"
            f"Lien : {e.url}"
            for e in events
        ])

        parts = [f"Un utilisateur recherche : '{query}'."]

        if profile:
            parts.append(
                f"\nProfil de l'utilisateur :\n{profile.to_prompt_context()}\n"
            )

        parts.append(
            f"Voici une liste d'evenements pertinents :\n\n{event_details}\n"
        )

        if profile and profile.openness < 0.3:
            parts.append(
                "Recommande uniquement des evenements qui correspondent "
                "aux genres et villes preferes de l'utilisateur."
            )
        elif profile and profile.openness < 0.7:
            parts.append(
                "Privilegie les evenements qui correspondent aux gouts de l'utilisateur, "
                "mais propose aussi une decouverte parmi les resultats."
            )
        elif profile:
            parts.append(
                "Propose un maximum de diversite et de decouverte, "
                "tout en expliquant pourquoi chaque evenement pourrait plaire a l'utilisateur."
            )
        else:
            parts.append(
                "En te basant uniquement sur ces evenements, recommande 3 evenements maximum "
                "et explique brievement pourquoi chacun correspond bien a ce que recherche l'utilisateur."
            )

        parts.append(
            "Pour chaque recommandation, inclus imperativement le lien de billetterie fourni "
            "dans le champ 'Lien' afin que l'utilisateur puisse reserver directement."
        )

        return "\n".join(parts)
