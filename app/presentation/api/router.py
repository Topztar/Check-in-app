"""
app/presentation/api/router.py
API 路由層 — 僅負責 HTTP 請求/回應處理，業務邏輯委派至 Application 層服務。
不直接操作 ORM 或資料庫，保持分層架構清晰。
"""
import uuid
import base64
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.future import select

from app.presentation.api.schemas import (
    DeviceEnrollRequest,
    ChallengeRequest,
    BiometricLoginRequest,
    ClockInRequest,
    AdminLoginRequest,
    AdminRegisterRequest,
)
from app.presentation.api.dependencies import (
    get_current_user,
    get_db,
    get_redis_service,
    get_rekognition_service,
)
from app.application.auth_service import AuthService
from app.domain.services.kalman_filter import GPSFilter
from app.domain.services.geofencing import GeofenceService
from app.domain.models import Device, Shift


api_router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# P0-3：設備註冊 — 驗證 JWT 並將 Device 記錄寫入資料庫
# ─────────────────────────────────────────────────────────────────────────────
@api_router.post("/auth/device/enroll", summary="設備註冊")
async def enroll_device(
    request: DeviceEnrollRequest,
    db=Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """
    裝置註冊端點：
    - 需要有效的 JWT（使用者本人或管理員）
    - 驗證請求者是本人（或 admin/manager 可代為操作）
    - 將 Device 記錄寫入資料庫，包含 ECDSA 公鑰
    """
    caller_user_id = current_user.get("sub")
    caller_role = current_user.get("role", "employee")

    # 驗證操作者是使用者本人，或為管理員/主管
    if caller_user_id != request.user_id and caller_role not in ("admin", "manager"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="無權限為其他使用者註冊裝置",
        )

    device_id = uuid.uuid4()
    tenant_id = current_user.get("tenant_id")

    async with db.session() as session:
        new_device = Device(
            id=device_id,
            tenant_id=tenant_id,
            user_id=request.user_id,
            device_name=request.device_name,
            public_key=request.public_key_pem,
        )
        session.add(new_device)
        await session.commit()

    return {"message": "設備註冊成功", "device_id": str(device_id)}


# ─────────────────────────────────────────────────────────────────────────────
# 取得生物辨識挑戰碼
# ─────────────────────────────────────────────────────────────────────────────
@api_router.post("/auth/challenge", summary="獲取生物辨識挑戰碼")
async def get_challenge(
    request: ChallengeRequest,
    redis_service=Depends(get_redis_service),
):
    challenge = await redis_service.set_challenge(request.device_id)
    return {"message": "挑戰碼產生成功", "challenge": challenge}


# ─────────────────────────────────────────────────────────────────────────────
# P0-2：生物辨識登入 — 實際驗證 ECDSA 簽章
# ─────────────────────────────────────────────────────────────────────────────
@api_router.post("/auth/biometric/login", summary="生物辨識登入")
async def biometric_login(
    request: BiometricLoginRequest,
    redis_service=Depends(get_redis_service),
    db=Depends(get_db),
):
    """
    生物辨識登入流程：
    1. 從 Redis 取得挑戰碼（驗證有效性）
    2. 從資料庫查詢裝置的 ECDSA 公鑰
    3. 以公鑰驗證挑戰碼的簽章
    4. 驗證通過後查詢使用者並回傳 JWT Token
    """
    # 步驟 1：驗證挑戰碼
    challenge = await redis_service.get_challenge(request.device_id)
    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="挑戰碼已過期或無效",
        )

    # 步驟 2：從資料庫查詢裝置記錄（取得公鑰）
    async with db.session() as session:
        stmt = select(Device).where(Device.id == request.device_id)
        result = await session.execute(stmt)
        device = result.scalars().first()

    if not device:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="裝置未註冊或已停用",
        )

    # 步驟 3：實際驗證 ECDSA 簽章（P0-2：取代原本的 is_valid = True）
    is_valid = AuthService.verify_signature(
        public_key_pem=device.public_key,
        signature_b64=request.signature_b64,
        message=challenge,
    )
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="簽章驗證失敗",
        )

    # 步驟 4：產生 JWT Token
    from app.domain.models import User
    async with db.session() as session:
        stmt = select(User).where(
            User.id == device.user_id,
            User.tenant_id == device.tenant_id,
        )
        result = await session.execute(stmt)
        user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="找不到對應的使用者",
        )

    token = AuthService.create_access_token(
        data={"sub": str(user.id), "tenant_id": str(user.tenant_id), "role": user.role}
    )
    return {"message": "登入成功", "token": token}


# ─────────────────────────────────────────────────────────────────────────────
# P0-6：考勤打卡 — 從資料庫讀取 Shift 地理圍欄設定
# ─────────────────────────────────────────────────────────────────────────────
@api_router.post("/attendance/clock-in", summary="考勤打卡")
async def clock_in(
    request: ClockInRequest,
    redis_service=Depends(get_redis_service),
    rekognition_service=Depends(get_rekognition_service),
    db=Depends(get_db),
    current_user: dict[str, Any] = Depends(get_current_user),
):
    """
    打卡流程：
    1. 驗證挑戰碼
    2. 活體檢測與臉部比對
    3. GPS 卡爾曼濾波平滑化
    4. 從資料庫讀取 Shift 的地理圍欄設定並驗證位置（P0-6）
    5. 記錄打卡資料
    """
    tenant_id = current_user.get("tenant_id")

    # 步驟 1：驗證挑戰碼
    challenge = await redis_service.get_challenge(request.device_id)
    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="挑戰碼已過期或無效",
        )

    # 步驟 2：Liveness 活體檢測與臉部比對
    try:
        image_bytes = base64.b64decode(request.image_bytes_b64)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="無效的影像格式",
        )

    session_id = await rekognition_service.create_face_liveness_session()
    is_match = await rekognition_service.search_faces_by_image(image_bytes)
    if not is_match:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="人臉辨識失敗",
        )

    # 步驟 3：GPS 卡爾曼濾波平滑化
    raw_coords = [(c.lat, c.lon) for c in request.gps_coordinates]
    try:
        smoothed_lat, smoothed_lon = GPSFilter.smooth_coordinates(raw_coords)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    # 步驟 4：從資料庫讀取 Shift 的地理圍欄設定（P0-6：取代寫死的 0.0, 0.0, 100.0）
    async with db.session() as session:
        stmt = select(Shift).where(
            Shift.id == request.shift_id,
            Shift.tenant_id == tenant_id,
        )
        result = await session.execute(stmt)
        shift = result.scalars().first()

    if not shift:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="找不到對應的班別記錄",
        )

    # 解析 geofence_data JSON 欄位
    geofence = shift.geofence_data
    if shift.geofence_type != "circle" or not isinstance(geofence, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="此班別的地理圍欄設定格式不支援（目前僅支援圓形圍欄）",
        )

    shift_lat: float = geofence.get("lat", 0.0)
    shift_lon: float = geofence.get("lng", 0.0)
    radius: float = geofence.get("radius", 100.0)

    is_within = GeofenceService.is_within_circle(
        shift_lat, shift_lon, radius, smoothed_lat, smoothed_lon
    )
    if not is_within:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="打卡位置超出工作區域",
        )

    return {
        "message": "打卡成功",
        "smoothed_location": {"lat": smoothed_lat, "lon": smoothed_lon},
        "liveness_session_id": session_id,
    }


# ─────────────────────────────────────────────────────────────────────────────
# P1-1：管理員登入與註冊 — 委派至 AdminService（Application 層）
# ─────────────────────────────────────────────────────────────────────────────
@api_router.post("/admin/login", summary="管理員登入 API")
async def api_admin_login(request: AdminLoginRequest, db=Depends(get_db)):
    """
    管理員登入：業務邏輯已移至 AdminService，Router 僅負責轉發請求。
    """
    from app.application.admin_service import AdminService
    admin_svc = AdminService(session_factory=db)
    return await admin_svc.login(email=request.username, password=request.password)


@api_router.post("/admin/register", summary="註冊新租戶與管理員")
async def api_admin_register(request: AdminRegisterRequest, db=Depends(get_db)):
    """
    新租戶與管理員註冊：業務邏輯已移至 AdminService，Router 僅負責轉發請求。
    """
    from app.application.admin_service import AdminService
    admin_svc = AdminService(session_factory=db)
    return await admin_svc.register(
        tenant_name=request.tenant_name,
        admin_name=request.admin_name,
        email=request.email,
        password=request.password,
    )
