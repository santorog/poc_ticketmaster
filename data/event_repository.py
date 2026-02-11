from client.eventbrite_client import EventbriteClient


class EventRepository:
    def __init__(self, client: EventbriteClient):
        self.client = client

    def get_events(self, query, location):
        pass  # Retourne une liste d’objets Event