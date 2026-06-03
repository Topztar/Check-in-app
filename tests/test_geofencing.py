import pytest
from app.domain.services.geofencing import GeofenceService

def test_haversine_distance():
    # San Francisco to San Jose approx distance is 68km
    lat1, lon1 = 37.7749, -122.4194
    lat2, lon2 = 37.3382, -121.8863
    dist = GeofenceService.haversine(lat1, lon1, lat2, lon2)
    assert 60000 < dist < 75000  # Should be around 68k meters

def test_is_within_circle():
    # 100 meters within 0,0
    assert GeofenceService.is_within_circle(0.0, 0.0, 100, 0.0005, 0.0005) is True
    assert GeofenceService.is_within_circle(0.0, 0.0, 100, 0.05, 0.05) is False

def test_ray_casting():
    polygon = [(0.0, 0.0), (0.0, 10.0), (10.0, 10.0), (10.0, 0.0)]
    assert GeofenceService.ray_casting((5.0, 5.0), polygon) is True
    assert GeofenceService.ray_casting((15.0, 5.0), polygon) is False
