import requests
from data.event import Event
from datetime import datetime, timezone, timedelta


class TicketmasterClient:
    BASE_URL = "https://app.ticketmaster.com/discovery/v2/"
    SEARCH_ENDPOINT = "events.json"
    DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
    DEFAULT_DAYS_START = 0
    DEFAULT_DAYS_END = 30
    DEFAULT_PAGE_SIZE = 20
    DEFAULT_MAX_PAGES = 3
    LOCALE = "fr-fr"

    ERROR_FETCH = "Erreur lors de la recuperation des evenements : "
    ERROR_EVENT_PARSE = "Erreur lors du parsing d'un evenement : "

    def __init__(self, api_key):
        self.api_key = api_key

    def fetch_events(self, query, city="Paris", start_days=DEFAULT_DAYS_START,
                     end_days=DEFAULT_DAYS_END, max_pages=DEFAULT_MAX_PAGES):
        url = f"{self.BASE_URL}{self.SEARCH_ENDPOINT}"

        now = datetime.now(timezone.utc)
        start_dt = (now + timedelta(days=start_days)).strftime(self.DATE_FORMAT)
        end_dt = (now + timedelta(days=end_days)).strftime(self.DATE_FORMAT)

        events = []
        page = 0

        while page < max_pages:
            params = {
                "apikey": self.api_key,
                "keyword": query,
                "city": city,
                "startDateTime": start_dt,
                "endDateTime": end_dt,
                "size": self.DEFAULT_PAGE_SIZE,
                "page": page,
                "locale": self.LOCALE,
                "sort": "date,asc",
            }

            response = requests.get(url, params=params)

            if response.status_code != 200:
                print(self.ERROR_FETCH + str(response.status_code))
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

        return events

    def _parse_event(self, event):
        genre = ""
        classifications = event.get("classifications", [])
        if classifications:
            genre = classifications[0].get("genre", {}).get("name", "")

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

        description_parts = []
        if genre:
            description_parts.append(genre)
        if venue_name:
            description_parts.append(f"au {venue_name}")
        if city_name:
            description_parts.append(f"a {city_name}")
        description = ", ".join(description_parts) if description_parts else ""

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
