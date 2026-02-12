from openai import OpenAI
from data.event import Event


class LLMClient:
    def __init__(self, api_key, model="gpt-3.5-turbo"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def generate_suggestion(self, query, events: [Event], profile=None, distances=None):
        prompt = self._build_prompt(query, events, profile, distances)

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
            "Tu connais parfaitement la scene culturelle francaise — musique, theatre, sport, danse, comedie, opera, tout. "
            "Tu parles comme un ami enthousiaste qui recommande ses coups de coeur. "
            "Tu donnes envie d'y aller en decrivant l'ambiance, ce qui rend l'evenement special. "
            "Tu adaptes tes recommandations au profil, aux gouts, au budget et a la localisation de la personne. "
            "CRITERES DE PRIORITE pour tes recommandations (du plus au moins important) :\n"
            "1. DISTANCE — privilegie les evenements proches de l'utilisateur\n"
            "2. GENRE — les evenements qui matchent ses gouts\n"
            "3. DATE — qui collent a ses disponibilites\n"
            "4. PRIX — dans son budget (si mentionne)\n"
            "5. QUALITE — la richesse de l'evenement, son ambiance\n"
            "Si un evenement est trop loin ou hors budget, ne le recommande pas.\n"
            "Tu tutoies l'utilisateur. "
            "Pour chaque recommandation, tu inclus TOUJOURS le lien de billetterie "
            "pour que la personne puisse reserver immediatement."
        )

    def _build_prompt(self, query, events: [Event], profile=None, distances=None):
        event_details = "\n\n".join([
            self._format_event(e, distances.get(e.id) if distances else None)
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

    def _format_event(self, e: Event, distance_km=None):
        lines = [
            f"Titre : {e.name}",
            f"Genre : {e.genre}",
            f"Lieu : {e.venue}",
            f"Ville : {e.city}",
            f"Date : {e.date}",
        ]
        if e.price:
            lines.append(f"Prix : {e.price:.0f} EUR")
        if distance_km is not None:
            lines.append(f"Distance : {distance_km} km")
        lines.append(f"Description : {e.description}")
        lines.append(f"Lien billetterie : {e.url}")
        return "\n".join(lines)
