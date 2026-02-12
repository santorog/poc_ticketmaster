import logging
import config
from log_config import setup_logging
from rag.vector_store import VectorStore
from rag.rag_engine import RagEngine
from rag.query_intent import diagnose_missing
from llm.llm_client import LLMClient
from data.user_profile import UserProfile

log = logging.getLogger("culturai.app")


def get_input(prompt_text):
    """Get input via voice or text."""
    print(f"\n{prompt_text}")
    print("  [v] Vocal (parler au micro)")
    print("  [t] Texte (taper au clavier)")
    choice = input("Choix (v/t) : ").strip().lower()

    if choice == "v":
        try:
            from voice.recorder import record_audio
            from voice.transcriber import transcribe

            audio_path = record_audio()
            if not audio_path:
                print("Aucun son enregistre.")
                return None

            print("Transcription en cours...")
            text = transcribe(audio_path, config.OPENAI_API_KEY)
            print(f'Tu as dit : "{text}"')
            return text
        except ImportError:
            print("Modules audio non installes (pip install sounddevice soundfile).")
            return None
        except Exception as e:
            print(f"Erreur audio : {e}")
            return None
    else:
        return input("> ")


def setup_profile():
    """Create or load user profile."""
    if UserProfile.exists():
        profile = UserProfile.load()
        print(f"\nSalut {profile.name} ! Content de te revoir.")
        print(f"  Tes gouts : {', '.join(profile.preferred_genres) or 'non definis'}")
        print(f"  Ta ville : {profile.city or 'non definie'}")
        if profile.search_city:
            print(f"  Recherche a : {profile.search_city}")
        if profile.budget_max:
            print(f"  Budget max : {profile.budget_max:.0f} EUR")

        reset = input("\nGarder ce profil ? (o/n) : ").strip().lower()
        if reset == "n":
            return create_profile()
        return profile

    return create_profile()


def create_profile():
    """Create a new profile from voice or text input."""
    print("\n--- Creation de ton profil ---")
    text = get_input(
        "Presente-toi ! Dis-moi ton prenom, ou tu habites, "
        "ce que tu aimes (musique, theatre, sport...), "
        "ou tu cherches des evenements en ce moment, "
        "quand tu es dispo, ton budget, "
        "et si tu es plutot du genre a rester dans tes gouts ou a decouvrir."
    )

    if not text:
        print("Profil vide, on continue sans.")
        return None

    print("Analyse de ton profil...")
    profile = UserProfile.from_transcription(text, config.OPENAI_API_KEY)
    profile.save()

    print(f"\nProfil cree !")
    print(f"  Prenom : {profile.name}")
    print(f"  Ville : {profile.city}")
    print(f"  Gouts : {', '.join(profile.preferred_genres)}")
    if profile.search_city:
        print(f"  Recherche a : {profile.search_city}")
    if profile.search_dates:
        print(f"  Dispo : {profile.search_dates}")
    if profile.budget_max:
        print(f"  Budget max : {profile.budget_max:.0f} EUR")
    print(f"  Ouverture : {profile.openness}/1.0")
    return profile


def main():
    setup_logging()

    print("=" * 50)
    print("  CulturAI — Ton conseiller culturel")
    print("=" * 50)

    vector_store = VectorStore(embedding_model="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

    if vector_store.load():
        print(f"Base chargee : {vector_store.count()} evenements indexes.")
    else:
        print("Aucune base trouvee. Lance d'abord : python ingest.py")
        return

    # Step 1: Profile
    profile = setup_profile()
    if profile:
        log.info("Profil charge : %s (ville=%s, search_city=%s, genres=%s, budget=%s)",
                 profile.name, profile.city, profile.search_city,
                 profile.preferred_genres, profile.budget_max)
    else:
        log.info("Pas de profil")

    # Step 2: Query
    user_query = get_input("Qu'est-ce qui te ferait plaisir ?")
    if not user_query:
        return

    log.info("Requete utilisateur : %s", user_query)
    print("\nAnalyse de ta recherche...")

    llm_client = LLMClient(config.OPENAI_API_KEY)
    rag_engine = RagEngine(vector_store, llm_client, api_key=config.OPENAI_API_KEY)

    # PASS 1: query-only
    response, is_good, intent = rag_engine.generate_response(user_query, profile=profile)

    if response and is_good:
        # Good results — display directly
        log.info("Passe 1 suffisante -> affichage direct")
        print(response)
        return

    if response:
        # Mediocre results
        log.info("Passe 1 mediocre -> proposition passe 2")
        missing = diagnose_missing(intent)
        print(f"\nJ'ai trouve quelques resultats, mais ils ne sont pas terribles.")
        if missing:
            print(f"({missing})")
        print("\nQue veux-tu faire ?")
        print("  [p] Preciser ta recherche")
        if profile:
            print("  [e] Enrichir avec ton profil")
        print("  [v] Voir quand meme les resultats")
        choice = input("Choix : ").strip().lower()
        log.info("Choix utilisateur : [%s]", choice)

        if choice == "p":
            refinement = get_input("Precise ta recherche :")
            if refinement:
                log.info("Precision utilisateur : %s", refinement)
                print("\nNouvelle recherche...")
                response2 = rag_engine.generate_refined_response(
                    user_query, refinement, profile=profile)
                print(response2 or "Toujours rien... essaie autre chose !")
            return

        if choice == "e" and profile:
            log.info("Enrichissement avec profil demande")
            print("\nRecherche enrichie avec ton profil...")
            response2 = rag_engine.generate_enriched_response(
                user_query, profile, intent)
            print(response2 or "Rien de mieux avec le profil.")
            return

        # [v] or other — show mediocre results
        log.info("Affichage des resultats mediocres")
        print(f"\n{response}")
    else:
        # No results at all
        log.info("Passe 1 : aucun resultat")
        print("\nAucun evenement ne correspond a ces criteres.")
        missing = diagnose_missing(intent)
        if missing:
            print(f"({missing})")
        print("Essaie d'elargir ta recherche : autre ville, autre genre, ou budget plus large.")
        if profile:
            enrich = input("Enrichir avec ton profil ? (o/n) : ").strip().lower()
            if enrich == "o":
                log.info("Enrichissement avec profil demande (depuis 0 resultats)")
                response2 = rag_engine.generate_enriched_response(
                    user_query, profile, intent)
                print(response2 or "Rien non plus avec le profil.")


if __name__ == "__main__":
    main()
