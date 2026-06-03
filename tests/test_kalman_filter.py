import pytest
from app.domain.services.kalman_filter import GPSFilter

def test_smooth_coordinates():
    raw_coords = [
        (37.7749, -122.4194),
        (37.7750, -122.4195),
        (37.7751, -122.4193),
        (37.7748, -122.4196)
    ]
    
    smoothed_lat, smoothed_lon = GPSFilter.smooth_coordinates(raw_coords)
    
    # Check if they are somewhat close to the input average
    assert 37.77 < smoothed_lat < 37.78
    assert -122.42 < smoothed_lon < -122.41
