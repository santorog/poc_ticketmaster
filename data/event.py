from dataclasses import dataclass, field


@dataclass
class Event:
    id: str
    name: str
    description: str
    date: str
    url: str
    venue: str = ""
    city: str = ""
    genre: str = ""

    def to_text(self):
        parts = [f"Concert : {self.name}"]
        if self.genre:
            parts.append(f"Genre musical : {self.genre}")
        if self.venue:
            parts.append(f"Salle : {self.venue}")
        if self.city:
            parts.append(f"Ville : {self.city}")
        if self.date:
            parts.append(f"Date : {self.date}")
        if self.description:
            parts.append(self.description)
        return ". ".join(parts)
