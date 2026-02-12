import config
from rag.vector_store import VectorStore
from rag.rag_engine import RagEngine
from llm.llm_client import LLMClient


def get_query():
    """Prompt the user to speak or type their query."""
    print("\nComment veux-tu chercher ?")
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
            print(f"Tu as dit : \"{text}\"")
            return text
        except ImportError:
            print("Modules audio non installes (pip install sounddevice soundfile).")
            return None
        except Exception as e:
            print(f"Erreur audio : {e}")
            return None
    else:
        return input("Que recherches-tu ? ")


def main():
    vector_store = VectorStore(embedding_model="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

    if vector_store.load():
        print(f"Base chargee : {vector_store.count()} evenements indexes.")
    else:
        print("Aucune base trouvee. Lance d'abord : python ingest.py")
        return

    user_query = get_query()
    if not user_query:
        return

    results = vector_store.query(user_query, top_k=10)
    if not results:
        print("Aucun evenement correspondant.")
        return

    print(f"\n{len(results)} evenements trouves, generation de la recommandation...\n")

    llm_client = LLMClient(config.OPENAI_API_KEY)
    rag_engine = RagEngine(vector_store, llm_client)

    response = rag_engine.generate_response(user_query)
    print(response)


if __name__ == "__main__":
    main()
