import os
import sqlite3
from datetime import datetime, timezone
from data.event import Event


class EventDatabase:
    DEFAULT_PATH = "db/events.db"

    CREATE_TABLE = """
        CREATE TABLE IF NOT EXISTS events (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            date TEXT DEFAULT '',
            url TEXT DEFAULT '',
            venue TEXT DEFAULT '',
            city TEXT DEFAULT '',
            genre TEXT DEFAULT '',
            classification TEXT DEFAULT '',
            fetched_at TEXT NOT NULL
        )
    """

    UPSERT = """
        INSERT INTO events (id, name, description, date, url, venue, city, genre, classification, fetched_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            name=excluded.name, description=excluded.description,
            date=excluded.date, url=excluded.url, venue=excluded.venue,
            city=excluded.city, genre=excluded.genre,
            classification=excluded.classification, fetched_at=excluded.fetched_at
    """

    SELECT_ALL = "SELECT id, name, description, date, url, venue, city, genre FROM events"

    def __init__(self, db_path=DEFAULT_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.execute(self.CREATE_TABLE)
        self.conn.commit()

    def upsert_events(self, events, classification=""):
        now = datetime.now(timezone.utc).isoformat()
        rows = [
            (e.id, e.name, e.description, e.date, e.url, e.venue, e.city, e.genre, classification, now)
            for e in events
        ]
        self.conn.executemany(self.UPSERT, rows)
        self.conn.commit()

    def get_all_events(self):
        cursor = self.conn.execute(self.SELECT_ALL)
        return [Event(id=r[0], name=r[1], description=r[2], date=r[3],
                      url=r[4], venue=r[5], city=r[6], genre=r[7])
                for r in cursor.fetchall()]

    def get_events_by_classification(self, classification):
        cursor = self.conn.execute(
            self.SELECT_ALL + " WHERE classification = ?", (classification,))
        return [Event(id=r[0], name=r[1], description=r[2], date=r[3],
                      url=r[4], venue=r[5], city=r[6], genre=r[7])
                for r in cursor.fetchall()]

    def count(self):
        return self.conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]

    def stats(self):
        genres = self.conn.execute(
            "SELECT genre, COUNT(*) FROM events GROUP BY genre ORDER BY COUNT(*) DESC LIMIT 15"
        ).fetchall()
        cities = self.conn.execute(
            "SELECT city, COUNT(*) FROM events GROUP BY city ORDER BY COUNT(*) DESC LIMIT 15"
        ).fetchall()
        classifications = self.conn.execute(
            "SELECT classification, COUNT(*) FROM events GROUP BY classification ORDER BY COUNT(*) DESC"
        ).fetchall()
        return {"genres": genres, "cities": cities, "classifications": classifications}

    def close(self):
        self.conn.close()
