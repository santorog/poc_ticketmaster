from client.ticketmaster_client import TicketmasterClient


class EventRepository:
    def __init__(self, client: TicketmasterClient):
        self.client = client

    def get_events(self, country_code="FR", classification_name=None, keyword=None):
        return self.client.fetch_events(
            country_code=country_code,
            classification_name=classification_name,
            keyword=keyword,
        )
