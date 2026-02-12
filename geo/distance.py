import math

# Coordinates of major French cities (latitude, longitude)
CITY_COORDS = {
    "paris": (48.8566, 2.3522),
    "marseille": (43.2965, 5.3698),
    "lyon": (45.7640, 4.8357),
    "toulouse": (43.6047, 1.4442),
    "nice": (43.7102, 7.2620),
    "nantes": (47.2184, -1.5536),
    "strasbourg": (48.5734, 7.7521),
    "montpellier": (43.6108, 3.8767),
    "bordeaux": (44.8378, -0.5792),
    "lille": (50.6292, 3.0573),
    "rennes": (48.1173, -1.6778),
    "reims": (49.2583, 3.2794),
    "toulon": (43.1242, 5.9280),
    "saint-etienne": (45.4397, 4.3872),
    "le havre": (49.4944, 0.1079),
    "grenoble": (45.1885, 5.7245),
    "dijon": (47.3220, 5.0415),
    "angers": (47.4784, -0.5632),
    "nimes": (43.8367, 4.3601),
    "clermont-ferrand": (45.7772, 3.0870),
    "clermont ferrand": (45.7772, 3.0870),
    "aix-en-provence": (43.5297, 5.4474),
    "brest": (48.3904, -4.4861),
    "tours": (47.3941, 0.6848),
    "amiens": (49.8941, 2.2958),
    "limoges": (45.8315, 1.2578),
    "perpignan": (42.6986, 2.8956),
    "metz": (49.1193, 6.1757),
    "besancon": (47.2378, 6.0241),
    "orleans": (47.9029, 1.9093),
    "rouen": (49.4432, 1.0999),
    "caen": (49.1829, -0.3707),
    "nancy": (48.6921, 6.1844),
    "avignon": (43.9493, 4.8055),
    "poitiers": (46.5802, 0.3404),
    "cannes": (43.5528, 7.0174),
    "pau": (43.2951, -0.3708),
    "la rochelle": (46.1603, -1.1511),
    "saint-malo": (48.6493, -2.0007),
    "biarritz": (43.4832, -1.5586),
    "colmar": (48.0794, 7.3588),
    "ajaccio": (41.9192, 8.7386),
    "dunkerque": (51.0343, 2.3768),
    "valence": (44.9334, 4.8924),
    "troyes": (48.2973, 4.0744),
    "chambery": (45.5646, 5.9178),
    "annecy": (45.8992, 6.1294),
    "saint-denis": (48.9362, 2.3574),
    "boulogne-billancourt": (48.8397, 2.2399),
    "boulogne billancourt": (48.8397, 2.2399),
    "marne-la-vallee": (48.8527, 2.7732),
    "marne la vallee": (48.8527, 2.7732),
    "marne la vallee cedex 4": (48.8527, 2.7732),
    "st herblain": (47.2122, -1.6497),
    "saint-herblain": (47.2122, -1.6497),
    "toulouse cedex 5": (43.6047, 1.4442),
}


def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance in km between two points using the Haversine formula."""
    R = 6371  # Earth radius in km

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def get_city_coords(city_name):
    """Look up coordinates for a French city. Returns (lat, lon) or None."""
    if not city_name:
        return None
    return CITY_COORDS.get(city_name.lower().strip())


def compute_distance(city_name, event):
    """Compute distance in km from a city to an event. Returns None if not computable."""
    origin = get_city_coords(city_name)
    if not origin:
        return None
    if not event.latitude or not event.longitude:
        return None
    return round(haversine(origin[0], origin[1], event.latitude, event.longitude))
