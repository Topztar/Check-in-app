import pytest
from datetime import datetime, timedelta
from app.domain.services.shift_service import ShiftService

def test_shift_details():
    # Standard 8-hour shift
    clock_in = datetime(2024, 1, 1, 9, 0, 0)
    clock_out = datetime(2024, 1, 1, 17, 0, 0)
    
    details = ShiftService.calculate_shift_details(clock_in, clock_out)
    assert details["total_hours"] == 8.0
    assert details["regular_hours"] == 8.0
    assert details["overtime_hours"] == 0.0
    assert details["overnight_premium_hours"] == 0.0

def test_shift_overtime():
    # 10-hour shift
    clock_in = datetime(2024, 1, 1, 9, 0, 0)
    clock_out = datetime(2024, 1, 1, 19, 0, 0)
    
    details = ShiftService.calculate_shift_details(clock_in, clock_out)
    assert details["total_hours"] == 10.0
    assert details["regular_hours"] == 8.0
    assert details["overtime_hours"] == 2.0
    assert details["overnight_premium_hours"] == 0.0

def test_shift_overnight():
    # Cross-midnight shift 20:00 to 04:00 (8 hours)
    # Overnight is 22:00 to 06:00, so 22:00 to 04:00 = 6 hours
    clock_in = datetime(2024, 1, 1, 20, 0, 0)
    clock_out = datetime(2024, 1, 2, 4, 0, 0)
    
    details = ShiftService.calculate_shift_details(clock_in, clock_out)
    assert details["total_hours"] == 8.0
    assert details["regular_hours"] == 8.0
    assert details["overtime_hours"] == 0.0
    # Floating point precision can be slightly off
    assert abs(details["overnight_premium_hours"] - 6.0) < 0.1
