import config
from client.ticketmaster_client import TicketmasterClient
from data.event_repository import EventRepository
from rag.vector_store import VectorStore
from rag.rag_engine import RagEngine
from llm.llm_client import LLMClient


def main():
    user_query = input("Que recherches-tu ? ")

    tm_client = TicketmasterClient(config.TICKETMASTER_API_KEY)
    repository = EventRepository(tm_client)
    events = repository.get_events(query=user_query, location="Paris")

    if not events:
        print("Aucun evenement trouve.")
        return

    vector_store = VectorStore(embedding_model="sentence-transformers/all-MiniLM-L6-v2")
    vector_store.add_events(events)

    llm_client = LLMClient(config.OPENAI_API_KEY)
    rag_engine = RagEngine(vector_store, llm_client)

    response = rag_engine.generate_response(user_query)
    print(response)


if __name__ == "__main__":
    main()
