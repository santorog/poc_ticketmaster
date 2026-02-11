import unittest
import os
from dotenv import load_dotenv
from client.ticketmaster_client import TicketmasterClient
from data.event import Event


class TestTicketmasterIntegration(unittest.TestCase):
    def setUp(self):
        load_dotenv()
        self.api_key = os.getenv("TICKETMASTER_CONSUMER_KEY")
        if not self.api_key:
            raise RuntimeError("TICKETMASTER_CONSUMER_KEY is not set in the environment.")
        self.client = TicketmasterClient(api_key=self.api_key)

    def test_fetch_music_events_in_france(self):
        events = self.client.fetch_events(
            country_code="FR", classification_name="music", page_size=5)

        self.assertIsInstance(events, list)
        self.assertGreater(len(events), 0)

        for e in events:
            self.assertIsInstance(e, Event)
            self.assertTrue(e.name)
            self.assertTrue(e.url)

    def test_fetch_returns_empty_for_nonsense_keyword(self):
        events = self.client.fetch_events(
            country_code="FR", keyword="xyzzy9999zzz", page_size=5)

        self.assertIsInstance(events, list)
        self.assertEqual(len(events), 0)


if __name__ == "__main__":
    unittest.main()
