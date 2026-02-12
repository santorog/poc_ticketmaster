import logging
from dataclasses import dataclass, field
from geo.distance import compute_distance

log = logging.getLogger("culturai.filters")

DEFAULT_RADIUS_KM = 50
MAX_EVENTS = 20


@dataclass
class Filters:
    city: str = ""
    max_distance_km: int = 0
    genres: list = field(default_factory=list)
    budget_max: float = 0

    @property
    def is_empty(self):
        return not self.city and not self.genres and self.budget_max <= 0

    def describe(self):
        """Resume FR des filtres actifs pour les logs."""
        parts = []
        if self.city:
            parts.append(f"ville={self.city} ({self.max_distance_km}km)")
        if self.genres:
            parts.append(f"genres={self.genres}")
        if self.budget_max > 0:
            parts.append(f"budget<={self.budget_max}")
        return ", ".join(parts) if parts else "(aucun filtre)"


def _match_genre(event_genre, filter_genres):
    """Match genre: exact or substring bidirectional."""
    if not event_genre or not filter_genres:
        return False
    event_lower = event_genre.lower()
    for fg in filter_genres:
        fg_lower = fg.lower()
        if fg_lower == event_lower:
            return True
        if fg_lower in event_lower or event_lower in fg_lower:
            return True
    return False


def apply_filters(event_map, filters):
    """Apply hard filters to event_map. Returns (eligible_indices, distances_km).

    - Distance: events beyond max_distance_km are eliminated. Events without coords pass.
    - Genre: events not matching any filter genre are eliminated.
    - Budget: events over budget_max are eliminated. Events with price=0 (unknown) pass.
    """
    log.info("--- Application des filtres ---")
    log.info("Filtres : %s", filters.describe())
    log.info("Evenements totaux : %d", len(event_map))

    eligible = []
    distances_km = {}
    rejected_distance = 0
    rejected_genre = 0
    rejected_budget = 0

    for idx, event in event_map.items():
        # Distance filter
        if filters.city and filters.max_distance_km > 0:
            d = compute_distance(filters.city, event)
            if d is not None:
                distances_km[event.id] = d
                if d > filters.max_distance_km:
                    rejected_distance += 1
                    continue
            # d is None (no coords) → event passes

        # Genre filter
        if filters.genres:
            if not _match_genre(event.genre, filters.genres):
                rejected_genre += 1
                continue

        # Budget filter
        if filters.budget_max > 0:
            if event.price and event.price > filters.budget_max:
                rejected_budget += 1
                continue

        eligible.append(idx)

    log.info("Filtrage termine : %d eligibles, rejetes: distance=%d, genre=%d, budget=%d",
             len(eligible), rejected_distance, rejected_genre, rejected_budget)

    return eligible, distances_km


def evaluate_results(count):
    """Evaluate result quality based on count alone."""
    is_good = count >= 3
    log.info("Evaluation : count=%d, is_good=%s", count, is_good)
    return is_good
