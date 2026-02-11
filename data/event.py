from dataclasses import dataclass

@dataclass
class Event:
    id: str
    name: str
    description: str
    date: str
    url: str