from client.ticketmaster_client import TicketmasterClient


class EventRepository:
    def __init__(self, client: TicketmasterClient):
        self.client = client

    def get_events(self, query, location="Paris"):
        return self.client.fetch_events(query=query, city=location)
