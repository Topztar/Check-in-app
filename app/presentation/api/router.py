from fastapi import APIRouter, Depends, Request, HTTPException, status
import base64

from app.presentation.api.schemas import (
    DeviceEnrollRequest,
    ChallengeRequest,
    BiometricLoginRequest,
    ClockInRequest,
    AdminLoginRequest,
    AdminRegisterRequest
)
from app.application.auth_service import AuthService
from app.domain.services.kalman_filter import GPSFilter
from app.domain.services.geofencing import GeofenceService

from sqlalchemy.future import select
from app.domain.models import Tenant, User


api_router = APIRouter()


def get_db(request: Request):
    return request.app.container.db()


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
async def api_admin_login(request: AdminLoginRequest, db = Depends(get_db)):
    async with db.session() as session:
        stmt = select(User).where(User.email == request.username)
        result = await session.execute(stmt)
        user = result.scalars().first()
        
        if not user or not AuthService.verify_password(request.password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="帳號或密碼錯誤")
            
        token = AuthService.create_access_token(data={"sub": str(user.id), "tenant_id": str(user.tenant_id), "role": user.role})
        return {"message": "登入成功", "token": token}

@api_router.post("/admin/register", summary="註冊新租戶與管理員")
async def api_admin_register(request: AdminRegisterRequest, db = Depends(get_db)):
    async with db.session() as session:
        # Check if user already exists
        stmt = select(User).where(User.email == request.email)
        result = await session.execute(stmt)
        if result.scalars().first():
            raise HTTPException(status_code=400, detail="此 Email 已被註冊")
            
        # Create Tenant
        new_tenant = Tenant(name=request.tenant_name)
        session.add(new_tenant)
        await session.flush() # To get tenant ID
        
        # Create User
        hashed_pw = AuthService.get_password_hash(request.password)
        new_user = User(
            tenant_id=new_tenant.id,
            email=request.email,
            name=request.admin_name,
            role="admin",
            hashed_password=hashed_pw
        )
        session.add(new_user)
        await session.commit()
        
        return {"message": "註冊成功，請導向登入頁面"}
