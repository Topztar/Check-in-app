from fastapi import APIRouter, Depends, HTTPException, status
from dependency_injector.wiring import inject, Provide
from typing import Annotated

from app.presentation.api.schemas import (
    DeviceEnrollRequest,
    ChallengeRequest,
    BiometricLoginRequest,
    ClockInRequest
)
from app.infrastructure.containers import Container
from app.infrastructure.services.redis_mock import RedisMockService
from app.infrastructure.services.rekognition_mock import RekognitionMockService
from app.application.auth_service import AuthService
from app.domain.services.kalman_filter import GPSFilter
from app.domain.services.geofencing import GeofenceService
import base64

api_router = APIRouter()

@api_router.post("/auth/device/enroll", summary="設備註冊")
async def enroll_device(request: DeviceEnrollRequest):
    # In a real app, you would save this to the database
    return {"message": "設備註冊成功", "device_id": "mock-device-id"}

@api_router.post("/auth/challenge", summary="獲取生物辨識挑戰碼")
@inject
async def get_challenge(
    request: ChallengeRequest,
    redis_service: RedisMockService = Depends(Provide[Container.redis_service])
):
    challenge = await redis_service.set_challenge(request.device_id)
    return {"message": "挑戰碼產生成功", "challenge": challenge}

@api_router.post("/auth/biometric/login", summary="生物辨識登入")
@inject
async def biometric_login(
    request: BiometricLoginRequest,
    redis_service: RedisMockService = Depends(Provide[Container.redis_service])
):
    challenge = await redis_service.get_challenge(request.device_id)
    if not challenge:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="挑戰碼已過期或無效")
        
    # In a real app, retrieve the user's public_key_pem from the database using device_id
    # Mocking verify_signature for now
    # is_valid = AuthService.verify_signature(public_key_pem, request.signature_b64, challenge)
    is_valid = True # mock
    
    if not is_valid:
         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="簽章驗證失敗")
         
    return {"message": "登入成功", "token": "mock-jwt-token"}

@api_router.post("/attendance/clock-in", summary="考勤打卡")
@inject
async def clock_in(
    request: ClockInRequest,
    redis_service: RedisMockService = Depends(Provide[Container.redis_service]),
    rekognition_service: RekognitionMockService = Depends(Provide[Container.rekognition_service])
):
    # 1. Validate biometric signature (similar to login)
    challenge = await redis_service.get_challenge(request.device_id)
    if not challenge:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="挑戰碼已過期或無效")
        
    # 2. Liveness & Face match
    try:
        image_bytes = base64.b64decode(request.image_bytes_b64)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="無效的影像格式")
        
    session_id = await rekognition_service.create_face_liveness_session()
    is_match = await rekognition_service.search_faces_by_image(image_bytes)
    if not is_match:
         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="人臉辨識失敗")
         
    # 3. Process GPS with Kalman Filter
    raw_coords = [(c.lat, c.lon) for c in request.gps_coordinates]
    try:
        smoothed_lat, smoothed_lon = GPSFilter.smooth_coordinates(raw_coords)
    except ValueError as e:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
         
    # 4. Check Geofence (Mocking a shift geofence at center 0,0 with 100m radius)
    shift_lat, shift_lon, radius = 0.0, 0.0, 100.0
    is_within = GeofenceService.is_within_circle(shift_lat, shift_lon, radius, smoothed_lat, smoothed_lon)
    if not is_within:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="打卡位置超出工作區域")
        
    # 5. In a real app, record the attendance to DB and calculate shift logic
    return {
        "message": "打卡成功",
        "smoothed_location": {"lat": smoothed_lat, "lon": smoothed_lon},
        "liveness_session_id": session_id
    }
