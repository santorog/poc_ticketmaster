from client.ticketmaster_client import TicketmasterClient


class EventRepository:
    def __init__(self, client: TicketmasterClient):
        self.client = client

    def get_events(self, query, country_code="FR"):
        return self.client.fetch_events(query=query, country_code=country_code)
