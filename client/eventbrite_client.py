import requests
from data.event import Event
from datetime import datetime, timezone, timedelta

class EventbriteClient:
    BASE_URL = "https://www.eventbriteapi.com/v3/"
    AUTH_ENDPOINT= "/users/me/"
    SEARCH_ENDPOINT = "events/search/"
    CONTENT_TYPE = "application/json"
    AUTH_HEADER = "Authorization"
    CONTENT_TYPE_HEADER = "Content-Type"
    DATE_FORMAT_SUFFIX = "Z"
    DEFAULT_DAYS_START = 0
    DEFAULT_DAYS_END = 30
    DEFAULT_MAX_PAGES = 3

    ERROR_FETCH = "Error while retrieving events: "
    ERROR_EVENT_PARSE = "Error while parsing event: "

    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
            self.AUTH_HEADER: f"Bearer {self.api_key}",
            self.CONTENT_TYPE_HEADER: self.CONTENT_TYPE
        }

    def fetch_events(self, query, location, start_days=DEFAULT_DAYS_START, end_days=DEFAULT_DAYS_END, max_pages=DEFAULT_MAX_PAGES):
        url = f"{self.BASE_URL}{self.SEARCH_ENDPOINT}"

        now = datetime.now(timezone.utc)
        range_start = (now + timedelta(days=start_days)).isoformat() + self.DATE_FORMAT_SUFFIX
        range_end = (now + timedelta(days=end_days)).isoformat() + self.DATE_FORMAT_SUFFIX

        events = []
        page = 1

        while page <= max_pages:
            params = {
                "q": query,
                "location.address": location,
                "start_date.range_start": range_start,
                "start_date.range_end": range_end,
                "page": page
            }

            response = requests.get(url, headers=self.headers, params=params)

            if response.status_code != 200:
                print(self.ERROR_FETCH + str(response.status_code))
                break

            data = response.json()
            for event in data.get("events", []):
                try:
                    events.append(Event(
                        id=event["id"],
                        name=event["name"]["text"],
                        description=event["description"]["text"] if event.get("description") else "",
                        date=event["start"]["local"],
                        url=event["url"]
                    ))
                except Exception as ex:
                    print(self.ERROR_EVENT_PARSE + str(ex))

            if not data.get("pagination", {}).get("has_more_items", False):
                break

            page += 1

        return events
