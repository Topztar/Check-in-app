class KalmanFilter:
    """
    A simple 1D Kalman filter implementation for smoothing GPS coordinates.
    Since latitude and longitude are independent, we can apply it separately to both.
    """
    def __init__(self, process_noise: float = 1e-5, measurement_noise: float = 1e-4):
        self.q = process_noise  # process noise covariance
        self.r = measurement_noise  # measurement noise covariance
        self.p = 1.0  # estimation error covariance
        self.x = 0.0  # value

    def update(self, measurement: float):
        # Prediction update
        self.p = self.p + self.q

        # Measurement update
        k = self.p / (self.p + self.r)
        self.x = self.x + k * (measurement - self.x)
        self.p = (1 - k) * self.p

        return self.x

class GPSFilter:
    @staticmethod
    def smooth_coordinates(coordinates: list[tuple[float, float]]) -> tuple[float, float]:
        """
        Takes an array of (lat, lon) coordinates and returns a single smoothed (lat, lon)
        using Kalman filtering.
        """
        if not coordinates:
            raise ValueError("Coordinates array cannot be empty")
            
        kf_lat = KalmanFilter()
        kf_lon = KalmanFilter()
        
        # Initialize with first coordinate
        kf_lat.x = coordinates[0][0]
        kf_lon.x = coordinates[0][1]
        
        smoothed_lat = coordinates[0][0]
        smoothed_lon = coordinates[0][1]
        
        for lat, lon in coordinates[1:]:
            smoothed_lat = kf_lat.update(lat)
            smoothed_lon = kf_lon.update(lon)
            
        return smoothed_lat, smoothed_lon
