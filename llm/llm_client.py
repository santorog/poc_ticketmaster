import logging
from openai import OpenAI
from data.event import Event

log = logging.getLogger("culturai.llm_client")


class LLMClient:
    def __init__(self, api_key, model="gpt-3.5-turbo"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def generate_suggestion(self, query, ranked_events, profile=None, distances=None):
        """Generate recommendation from ranked events.

        Args:
            ranked_events: list of (Event, l2_distance) tuples from FAISS
        """
        prompt = self._build_prompt(query, ranked_events, profile, distances)
        system = self._system_prompt()

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ]

        log.info("--- Appel GPT recommandation ---")
        log.info("Modele : %s, temperature=0.8, max_tokens=3000", self.model)
        log.info("Evenements fournis au LLM : %d", len(ranked_events))
        log.debug("System prompt LLM",
                  extra={"json_data": {"system": system}})
        log.debug("User prompt LLM",
                  extra={"json_data": {"user_prompt": prompt}})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.8,
            max_tokens=3000,
        )

        result = response.choices[0].message.content.strip()

        log.debug("Reponse GPT recommandation",
                  extra={"json_data": {
                      "response_preview": result[:500],
                      "response_length": len(result),
                      "usage": {"prompt_tokens": response.usage.prompt_tokens,
                                "completion_tokens": response.usage.completion_tokens,
                                "total_tokens": response.usage.total_tokens}}})

        return result

    def _system_prompt(self):
        return (
            "Tu es CulturAI, un conseiller culturel passione et chaleureux. "
            "Tu connais parfaitement la scene culturelle francaise — musique, theatre, sport, danse, comedie, opera, tout. "
            "Tu parles comme un ami enthousiaste qui recommande ses coups de coeur. "
            "Tu donnes envie d'y aller en decrivant l'ambiance, ce qui rend l'evenement special. "
            "Tu adaptes tes recommandations au profil, aux gouts, au budget et a la localisation de la personne. "
            "Les evenements fournis ont deja ete filtres par ville, genre et budget — "
            "ils correspondent tous aux criteres de l'utilisateur. "
            "Ton role est de les presenter de maniere engageante et personnalisee.\n"
            "Si un evenement est trop loin ou hors budget, ne le recommande pas.\n"
            "Tu tutoies l'utilisateur. "
            "Pour chaque recommandation, tu inclus TOUJOURS le lien de billetterie "
            "pour que la personne puisse reserver immediatement.\n\n"
            "IMPORTANT — ADAPTE TON TON en fonction du nombre de resultats :\n"
            "- 10+ resultats : tu es surexcite, \"J'ai exactement ce qu'il te faut !\"\n"
            "- 3 a 9 resultats : ton chaleureux et confiant, \"J'ai de belles trouvailles pour toi\"\n"
            "- 1 a 2 resultats : ton honnete et bienveillant, "
            "\"J'ai pas trouve beaucoup de choix pour cette recherche, mais regarde quand meme ca\"\n"
            "Commence TOUJOURS ta reponse par une phrase d'accroche qui reflete le nombre de resultats. "
            "Sois transparent, jamais de faux enthousiasme."
        )

    def _build_prompt(self, query, ranked_events, profile=None, distances=None):
        count = len(ranked_events)

        event_details = "\n\n".join([
            self._format_event(e, distances.get(e.id) if distances else None)
            for e, _ in ranked_events
        ])

        parts = []

        if profile:
            parts.append(f"Profil de l'utilisateur :\n{profile.to_prompt_context()}")

        parts.append(f"L'utilisateur cherche : \"{query}\"")

        parts.append(f"{count} evenements correspondent a ses criteres.")

        parts.append(f"Voici les {count} evenements tries par pertinence semantique :\n\n{event_details}")
        parts.append(
            "Recommande tous les evenements qui valent le coup pour cette personne. "
            "Pour chacun, explique pourquoi ca va lui plaire en te basant sur ses gouts, "
            "donne envie avec une description vivante de l'ambiance, "
            "et inclus le lien de billetterie pour reserver. "
            "Si certains evenements ne sont vraiment pas adaptes, ecarte-les."
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
