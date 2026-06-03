from pydantic import BaseModel, Field
from typing import List, Tuple, Optional

class DeviceEnrollRequest(BaseModel):
    user_id: str
    device_name: str
    public_key_pem: str

class ChallengeRequest(BaseModel):
    device_id: str

class BiometricLoginRequest(BaseModel):
    device_id: str
    signature_b64: str

class GPSCoordinate(BaseModel):
    lat: float
    lon: float

class ClockInRequest(BaseModel):
    user_id: str
    shift_id: str
    device_id: str
    signature_b64: str
    gps_coordinates: List[GPSCoordinate] = Field(..., min_items=1, max_items=10)
    image_bytes_b64: str
