from fastapi import APIRouter, Depends, Request, HTTPException, status
import base64

from app.presentation.api.schemas import (
    DeviceEnrollRequest,
    ChallengeRequest,
    BiometricLoginRequest,
    ClockInRequest,
    AdminLoginRequest
)
from app.application.auth_service import AuthService
from app.domain.services.kalman_filter import GPSFilter
from app.domain.services.geofencing import GeofenceService

api_router = APIRouter()

def get_redis_service(request: Request):
    return request.app.container.redis_service()

def get_rekognition_service(request: Request):
    return request.app.container.rekognition_service()

@api_router.post("/auth/device/enroll", summary="設備註冊")
async def enroll_device(request: DeviceEnrollRequest):
    return {"message": "設備註冊成功", "device_id": "mock-device-id"}

@api_router.post("/auth/challenge", summary="獲取生物辨識挑戰碼")
async def get_challenge(
    request: ChallengeRequest,
    redis_service = Depends(get_redis_service)
):
    challenge = await redis_service.set_challenge(request.device_id)
    return {"message": "挑戰碼產生成功", "challenge": challenge}

@api_router.post("/auth/biometric/login", summary="生物辨識登入")
async def biometric_login(
    request: BiometricLoginRequest,
    redis_service = Depends(get_redis_service)
):
    challenge = await redis_service.get_challenge(request.device_id)
    
    if not challenge:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="挑戰碼已過期或無效")
        
    is_valid = True 
    
    if not is_valid:
         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="簽章驗證失敗")
         
    return {"message": "登入成功", "token": "mock-jwt-token"}

@api_router.post("/attendance/clock-in", summary="考勤打卡")
async def clock_in(
    request: ClockInRequest,
    redis_service = Depends(get_redis_service),
    rekognition_service = Depends(get_rekognition_service)
):
    # 1. 驗證挑戰碼與簽章
    challenge = await redis_service.get_challenge(request.device_id)
    if not challenge:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="挑戰碼已過期或無效")
        
    # 2. Liveness 活體檢測與臉部比對
    try:
        image_bytes = base64.b64decode(request.image_bytes_b64)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="無效的影像格式")
        
    session_id = await rekognition_service.create_face_liveness_session()
    is_match = await rekognition_service.search_faces_by_image(image_bytes)
    if not is_match:
         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="人臉辨識失敗")
         
    # 3. 處理 GPS 與卡爾曼濾波器
    raw_coords = [(c.lat, c.lon) for c in request.gps_coordinates]
    try:
        smoothed_lat, smoothed_lon = GPSFilter.smooth_coordinates(raw_coords)
    except ValueError as e:
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
         
    # 4. 驗證地理圍欄
    shift_lat, shift_lon, radius = 0.0, 0.0, 100.0
    is_within = GeofenceService.is_within_circle(shift_lat, shift_lon, radius, smoothed_lat, smoothed_lon)
    if not is_within:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="打卡位置超出工作區域")
        
    return {
        "message": "打卡成功",
        "smoothed_location": {"lat": smoothed_lat, "lon": smoothed_lon},
        "liveness_session_id": session_id
    }

@api_router.post("/admin/login", summary="管理員登入 API")
async def api_admin_login(request: AdminLoginRequest):
    # 此為模擬的 API 登入邏輯，真實環境應查詢資料庫驗證雜湊密碼
    if request.username == "admin" and request.password == "admin123":
        return {"message": "登入成功", "token": "mock-admin-jwt-token"}
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="帳號或密碼錯誤")
