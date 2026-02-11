import unittest
import os
from dotenv import load_dotenv
from client.eventbrite_client import EventbriteClient
from data.event import Event

class TestEventbriteIntegration(unittest.TestCase):
    def setUp(self):
        load_dotenv()
        self.api_key = os.getenv("EVENTBRITE_PRIVATE_TOKEN")
        if not self.api_key:
            raise RuntimeError("EVENTBRITE_PRIVATE_TOKEN is not set in the environment.")
        self.client = EventbriteClient(api_key=self.api_key)

    def test_fetch_jazz_events_in_paris(self):
        events = self.client.fetch_events(query="jazz", location="Paris", max_pages=1)

        self.assertIsInstance(events, list)
        self.assertGreater(len(events), 0)

        for e in events:
            self.assertIsInstance(e, Event)
            self.assertTrue(e.name)
            self.assertTrue(e.date)
            self.assertTrue(e.url)

if __name__ == "__main__":
    unittest.main()
