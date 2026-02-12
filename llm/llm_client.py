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
            messages=[
                {"role": "system", "content": self._system_prompt()},
                {"role": "user", "content": prompt},
            ],
            temperature=0.8,
            max_tokens=1500,
        )

        return response.choices[0].message.content.strip()

    def _system_prompt(self):
        return (
            "Tu es CulturAI, un conseiller culturel passione et chaleureux. "
            "Tu connais parfaitement la scene culturelle francaise. "
            "Tu parles comme un ami enthousiaste qui recommande ses coups de coeur. "
            "Tu donnes envie d'y aller en decrivant l'ambiance, ce qui rend l'evenement special. "
            "Tu adaptes tes recommandations au profil et aux gouts de la personne. "
            "Tu tutoies l'utilisateur. "
            "Pour chaque recommandation, tu inclus TOUJOURS le lien de billetterie "
            "pour que la personne puisse reserver immediatement."
        )

    def _build_prompt(self, query, events: [Event], profile=None):
        event_details = "\n\n".join([
            f"Titre : {e.name}\n"
            f"Genre : {e.genre}\n"
            f"Lieu : {e.venue}\n"
            f"Ville : {e.city}\n"
            f"Date : {e.date}\n"
            f"Description : {e.description}\n"
            f"Lien billetterie : {e.url}"
            for e in events
        ])

        parts = []

        if profile:
            parts.append(f"Profil de l'utilisateur :\n{profile.to_prompt_context()}")

        parts.append(f"L'utilisateur cherche : \"{query}\"")
        parts.append(f"Voici les evenements disponibles :\n\n{event_details}")
        parts.append(
            "Recommande les 3 meilleurs evenements pour cette personne. "
            "Pour chacun, explique pourquoi ca va lui plaire en te basant sur ses gouts, "
            "donne envie avec une description vivante de l'ambiance, "
            "et inclus le lien de billetterie pour reserver."
        )

        return "\n\n".join(parts)
