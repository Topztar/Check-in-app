from datetime import datetime, timedelta

class ShiftService:
    @staticmethod
    def calculate_shift_details(clock_in: datetime, clock_out: datetime) -> dict:
        """
        Calculates shift details including cross-midnight processing,
        overnight premium pay (if any hours are between 22:00 and 06:00),
        and standard overtime (hours > 8).
        """
        # Ensure total time is logical
        total_duration = clock_out - clock_in
        total_hours = total_duration.total_seconds() / 3600.0
        
        # Overtime calculation (Standard overtime over 8 hours)
        regular_hours = min(8.0, total_hours)
        overtime_hours = max(0.0, total_hours - 8.0)
        
        # Cross-midnight / overnight premium logic
        # Overnight is defined as 22:00 to 06:00 next day
        overnight_hours = 0.0
        current_time = clock_in
        while current_time < clock_out:
            next_time = current_time + timedelta(minutes=1)
            # If current minute falls between 22:00 and 06:00
            if current_time.hour >= 22 or current_time.hour < 6:
                overnight_hours += 1 / 60.0
            current_time = next_time

        return {
            "logical_shift_date": clock_in.date(), # Cross-midnight processing sets shift date to start date
            "total_hours": round(total_hours, 2),
            "regular_hours": round(regular_hours, 2),
            "overtime_hours": round(overtime_hours, 2),
            "overnight_premium_hours": round(overnight_hours, 2)
        }
