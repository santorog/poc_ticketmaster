import config
from client.eventbrite_client import EventbriteClient
from data.event_repository import EventRepository
from rag.vector_store import VectorStore


def main():
    user_query = input("Que recherches-tu ? ")

    eb_client = EventbriteClient(config.EVENTBRITE_TOKEN)
    repository = EventRepository(eb_client)
    events = repository.get_events(query=user_query, location="Paris")

    vector_store = VectorStore(embedding_model="sentence-transformers/all-MiniLM-L6-v2")
    vector_store.add_events(events)

    llm_client = (
        LLMClient(config.OPENAI_API_KEY))
    rag_engine = RagEngine(vector_store, llm_client)

    response = rag_engine.generate_response(user_query)
    print(response)


if __name__ == "__main__":
    main()
