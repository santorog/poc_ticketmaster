from openai import OpenAI
from data.event import Event


class LLMClient:
    def __init__(self, api_key, model="gpt-3.5-turbo"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def generate_suggestion(self, query, events: [Event]):
        prompt = self._build_prompt(query, events)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=500
        )

        return response.choices[0].message.content.strip()

    def _build_prompt(self, query, events: [Event]):
        event_details = "\n\n".join([
            f"Titre : {event.name}\nDescription : {event.description}\nDate : {event.date}\nLien : {event.url}"
            for event in events
        ])

        prompt = (
            f"Un utilisateur recherche : '{query}'.\n"
            f"Voici une liste d'événements pertinents :\n\n"
            f"{event_details}\n\n"
            f"En te basant uniquement sur ces événements, recommande 3 événements maximum "
            f"et explique brièvement pourquoi chacun correspond bien à ce que recherche l'utilisateur."
        )

        return prompt
