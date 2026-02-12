import time
import requests
from data.event import Event


class TicketmasterClient:
    BASE_URL = "https://app.ticketmaster.com/discovery/v2/"
    SEARCH_ENDPOINT = "events.json"
    DEFAULT_PAGE_SIZE = 200
    MAX_PAGE = 5
    LOCALE = "*"
    REQUEST_DELAY = 0.25

    ERROR_FETCH = "Erreur lors de la recuperation des evenements : "
    ERROR_EVENT_PARSE = "Erreur lors du parsing d'un evenement : "

    def __init__(self, api_key):
        self.api_key = api_key

    def fetch_events(self, country_code="FR", classification_name=None,
                     keyword=None, genre_id=None, page_size=DEFAULT_PAGE_SIZE):
        url = f"{self.BASE_URL}{self.SEARCH_ENDPOINT}"

        events = []
        page = 0

        while page <= self.MAX_PAGE:
            params = {
                "apikey": self.api_key,
                "countryCode": country_code,
                "size": page_size,
                "page": page,
                "locale": self.LOCALE,
            }
            if classification_name:
                params["classificationName"] = classification_name
            if keyword:
                params["keyword"] = keyword
            if genre_id:
                params["genreId"] = genre_id

            response = requests.get(url, params=params)

            if response.status_code != 200:
                print(f"{self.ERROR_FETCH}{response.status_code} (page {page})")
                break

            data = response.json()
            embedded = data.get("_embedded")
            if not embedded:
                break

            for event in embedded.get("events", []):
                try:
                    events.append(self._parse_event(event))
                except Exception as ex:
                    print(self.ERROR_EVENT_PARSE + str(ex))

            page_info = data.get("page", {})
            total_pages = page_info.get("totalPages", 1)
            page += 1
            if page >= total_pages:
                break

            time.sleep(self.REQUEST_DELAY)

        return events

    def _parse_event(self, event):
        genre = ""
        segment = ""
        subgenre = ""
        classifications = event.get("classifications", [])
        if classifications:
            cls = classifications[0]
            genre = cls.get("genre", {}).get("name", "")
            segment = cls.get("segment", {}).get("name", "")
            subgenre = cls.get("subGenre", {}).get("name", "")
            if genre in ("Undefined", "Other", ""):
                genre = subgenre if subgenre not in ("Undefined", "Other", "") else segment

        venue_name = ""
        city_name = ""
        venues = event.get("_embedded", {}).get("venues", [])
        if venues:
            venue_name = venues[0].get("name", "")
            city_name = venues[0].get("city", {}).get("name", "")

        date = ""
        dates = event.get("dates", {})
        start = dates.get("start", {})
        date = start.get("localDate", "")
        local_time = start.get("localTime", "")
        if local_time:
            date = f"{date} {local_time}"

        description = event.get("description", "") or event.get("info", "")
        if not description:
            parts = []
            if genre:
                parts.append(genre)
            if venue_name:
                parts.append(f"au {venue_name}")
            if city_name:
                parts.append(f"a {city_name}")
            description = ", ".join(parts) if parts else ""

        return Event(
            id=event["id"],
            name=event.get("name", ""),
            description=description,
            date=date,
            url=event.get("url", ""),
            venue=venue_name,
            city=city_name,
            genre=genre,
        )
