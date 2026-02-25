"""Tests for geospatial utilities."""


from app.utils.geo import approx_distance_miles, haversine_distance_miles, validate_coordinates


def test_haversine_same_point():
    """Distance from a point to itself should be zero."""
    assert haversine_distance_miles(29.0, -81.0, 29.0, -81.0) == 0.0


def test_haversine_known_distance():
    """Test against a known distance (NYC to LA ≈ 2451 miles)."""
    dist = haversine_distance_miles(40.7128, -74.0060, 34.0522, -118.2437)
    assert 2440 < dist < 2460


def test_approx_distance_short():
    """Approximate distance should be close to haversine for short distances."""
    lat1, lon1 = 29.0, -81.0
    lat2, lon2 = 29.01, -81.01
    exact = haversine_distance_miles(lat1, lon1, lat2, lon2)
    approx = approx_distance_miles(lat1, lon1, lat2, lon2)
    assert abs(exact - approx) < 0.2  # Within 0.2 miles for short distance


def test_validate_coordinates():
    assert validate_coordinates(29.0, -81.0) is True
    assert validate_coordinates(90, 180) is True
    assert validate_coordinates(-90, -180) is True
    assert validate_coordinates(91, 0) is False
    assert validate_coordinates(0, 181) is False


def test_validate_coordinates_edge_cases():
    assert validate_coordinates(0, 0) is True
    assert validate_coordinates(-90.001, 0) is False
