import config
from rag.vector_store import VectorStore
from rag.rag_engine import RagEngine
from llm.llm_client import LLMClient
from data.user_profile import UserProfile


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
    print(f"  Ouverture : {profile.openness}/1.0")
    return profile


def main():
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

    # Step 2: Query
    user_query = get_input("Qu'est-ce qui te ferait plaisir ?")
    if not user_query:
        return

    results = vector_store.query(user_query, top_k=10)
    if not results:
        print("Aucun evenement correspondant. Essaie une autre recherche !")
        return

    print(f"\n{len(results)} evenements trouves, je prepare mes recommandations...\n")

    llm_client = LLMClient(config.OPENAI_API_KEY)
    rag_engine = RagEngine(vector_store, llm_client)

    response = rag_engine.generate_response(user_query, profile=profile)
    print(response)


if __name__ == "__main__":
    main()
