import config
from rag.vector_store import VectorStore
from rag.rag_engine import RagEngine
from llm.llm_client import LLMClient


def main():
    vector_store = VectorStore(embedding_model="sentence-transformers/all-MiniLM-L6-v2")

    if vector_store.load():
        print(f"Base chargee : {vector_store.count()} evenements indexes.")
    else:
        print("Aucune base trouvee. Lance d'abord : python ingest.py")
        return

    user_query = input("Que recherches-tu ? ")

    results = vector_store.query(user_query, top_k=5)
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
