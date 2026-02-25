"""Geospatial utilities for distance calculations and coordinate handling."""

import math


def haversine_distance_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points in miles."""
    earth_radius = 3959  # miles

    lat1_r, lat2_r = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return earth_radius * c


def approx_distance_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Fast approximate distance in miles (Euclidean projection, US latitudes)."""
    dlat = abs(lat1 - lat2) * 69.0
    dlon = abs(lon1 - lon2) * 54.6
    return math.sqrt(dlat**2 + dlon**2)


def point_wkt(lon: float, lat: float) -> str:
    """Create a WKT POINT string (note: WKT is lon, lat order)."""
    return f"POINT({lon} {lat})"


def validate_coordinates(lat: float, lon: float) -> bool:
    """Check if coordinates are valid."""
    return -90 <= lat <= 90 and -180 <= lon <= 180


def score_to_severity_level(score: float) -> str:
    """Map a 0.0-1.0 severity score to a categorical level."""
    if score < 0.25:
        return "minor"
    elif score < 0.5:
        return "moderate"
    elif score < 0.75:
        return "severe"
    return "critical"
