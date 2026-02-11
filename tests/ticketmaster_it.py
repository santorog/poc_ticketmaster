import unittest
import os
from dotenv import load_dotenv
from client.ticketmaster_client import TicketmasterClient
from data.event import Event


class TestTicketmasterIntegration(unittest.TestCase):
    def setUp(self):
        load_dotenv()
        self.api_key = os.getenv("TICKETMASTER_API_KEY")
        if not self.api_key:
            raise RuntimeError("TICKETMASTER_API_KEY is not set in the environment.")
        self.client = TicketmasterClient(api_key=self.api_key)

    def test_fetch_jazz_events_in_paris(self):
        events = self.client.fetch_events(query="jazz", city="Paris", max_pages=1)

        self.assertIsInstance(events, list)
        self.assertGreater(len(events), 0)

        for e in events:
            self.assertIsInstance(e, Event)
            self.assertTrue(e.name)
            self.assertTrue(e.date)
            self.assertTrue(e.url)

    def test_fetch_returns_empty_for_nonsense_query(self):
        events = self.client.fetch_events(query="xyzzy9999zzz", city="Paris", max_pages=1)

        self.assertIsInstance(events, list)
        self.assertEqual(len(events), 0)


if __name__ == "__main__":
    unittest.main()
