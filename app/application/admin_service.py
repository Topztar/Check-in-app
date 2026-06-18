"""
app/application/admin_service.py
管理員應用服務 — 封裝租戶管理員的登入與註冊業務邏輯。
將資料庫操作從 Presentation 層（router.py）移至 Application 層，
維持清晰的分層架構：Presentation → Application → Domain → Infrastructure。
"""
from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.domain.models import Tenant, User, Device, Shift, AttendanceRecord
from app.application.auth_service import AuthService


class AdminService:
    """
    管理員相關業務邏輯服務。
    透過 session_factory (Database 實例) 取得資料庫連線。
    """

    def __init__(self, session_factory) -> None:
        # session_factory 是 Database 實例，提供 .session() 上下文管理器
        self._session_factory = session_factory

    async def login(self, email: str, password: str) -> dict:
        """
        管理員登入：
        1. 以 email 查詢使用者（全域查詢，不限租戶）
        2. 驗證密碼
        3. 產生並回傳 JWT Token

        TODO（P2-2）：未來多租戶登入應加入 tenant subdomain 限縮查詢範圍，
        避免不同租戶的同名 email 產生衝突。目前 email 在系統層級應唯一（見 P1-2 UniqueConstraint）。
        """
        async with self._session_factory.session() as session:
            stmt = select(User).where(User.email == email)
            result = await session.execute(stmt)
            user = result.scalars().first()

            if not user or not AuthService.verify_password(password, user.hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="帳號或密碼錯誤",
                )

            token = AuthService.create_access_token(
                data={
                    "sub": str(user.id),
                    "tenant_id": str(user.tenant_id),
                    "role": user.role,
                }
            )
            return {"message": "登入成功", "token": token}

    async def register(
        self,
        tenant_name: str,
        admin_name: str,
        email: str,
        password: str,
    ) -> dict:
        """
        新租戶與管理員註冊：
        1. 檢查 email 是否已存在
        2. 建立 Tenant 記錄
        3. 建立管理員 User 記錄（role="admin"）
        4. 提交並回傳成功訊息
        """
        async with self._session_factory.session() as session:
            # 檢查 Email 是否重複
            stmt = select(User).where(User.email == email)
            result = await session.execute(stmt)
            if result.scalars().first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="此 Email 已被註冊",
                )

            # 建立租戶
            new_tenant = Tenant(name=tenant_name)
            session.add(new_tenant)
            await session.flush()  # 取得 new_tenant.id 以建立關聯

            # 建立管理員使用者
            hashed_pw = AuthService.get_password_hash(password)
            new_user = User(
                tenant_id=new_tenant.id,
                email=email,
                name=admin_name,
                role="admin",
                hashed_password=hashed_pw,
            )
            session.add(new_user)
            await session.commit()

            return {"message": "註冊成功，請導向登入頁面"}

    async def get_dashboard_data(self, tenant_id_str: str) -> dict:
        """
        查詢特定租戶的管理後台統計資料。
        """
        import uuid
        try:
            tenant_id = uuid.UUID(tenant_id_str)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="無效的租戶 ID 格式",
            )

        async with self._session_factory.session() as session:
            # 取得租戶資料
            tenant_stmt = select(Tenant).where(Tenant.id == tenant_id)
            tenant = (await session.execute(tenant_stmt)).scalars().first()
            if not tenant:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="找不到指定的租戶資訊",
                )

            # 統計資訊
            user_count_stmt = select(func.count(User.id)).where(User.tenant_id == tenant_id)
            user_count = (await session.execute(user_count_stmt)).scalar() or 0

            device_count_stmt = select(func.count(Device.id)).where(Device.tenant_id == tenant_id)
            device_count = (await session.execute(device_count_stmt)).scalar() or 0

            shift_count_stmt = select(func.count(Shift.id)).where(Shift.tenant_id == tenant_id)
            shift_count = (await session.execute(shift_count_stmt)).scalar() or 0

            # 列表資訊
            users_stmt = select(User).where(User.tenant_id == tenant_id)
            users = (await session.execute(users_stmt)).scalars().all()

            shifts_stmt = select(Shift).where(Shift.tenant_id == tenant_id)
            shifts = (await session.execute(shifts_stmt)).scalars().all()

            # 考勤打卡記錄（聯集 User 與 Shift 取得員工與班別名稱）
            attendance_stmt = (
                select(AttendanceRecord, User.name.label("user_name"), Shift.name.label("shift_name"))
                .join(User, (AttendanceRecord.user_id == User.id) & (AttendanceRecord.tenant_id == User.tenant_id))
                .join(Shift, (AttendanceRecord.shift_id == Shift.id) & (AttendanceRecord.tenant_id == Shift.tenant_id))
                .where(AttendanceRecord.tenant_id == tenant_id)
                .order_by(AttendanceRecord.clock_in_time.desc())
                .limit(10)
            )
            attendance_results = (await session.execute(attendance_stmt)).all()

            attendance_list = []
            for row in attendance_results:
                record = row[0]
                attendance_list.append({
                    "id": str(record.id),
                    "user_id": str(record.user_id),
                    "user_name": row.user_name,
                    "shift_id": str(record.shift_id),
                    "shift_name": row.shift_name,
                    "clock_in_time": record.clock_in_time.isoformat() if record.clock_in_time else None,
                    "clock_out_time": record.clock_out_time.isoformat() if record.clock_out_time else None,
                    "latitude": record.latitude,
                    "longitude": record.longitude,
                    "status": record.status,
                    "clock_in_type": record.clock_in_type,
                })

            return {
                "tenant_name": tenant.name,
                "stats": {
                    "users_count": user_count,
                    "devices_count": device_count,
                    "shifts_count": shift_count,
                },
                "users": [{"id": str(u.id), "name": u.name, "email": u.email, "role": u.role} for u in users],
                "shifts": [
                    {
                        "id": str(s.id),
                        "name": s.name,
                        "start_time": s.start_time.isoformat() if s.start_time else None,
                        "end_time": s.end_time.isoformat() if s.end_time else None,
                        "geofence_type": s.geofence_type,
                        "geofence_data": s.geofence_data,
                    }
                    for s in shifts
                ],
                "attendance_records": attendance_list,
            }

    async def create_shift(
        self,
        tenant_id_str: str,
        name: str,
        start_time_str: str,
        end_time_str: str,
        geofence_type: str,
        geofence_data: dict,
    ) -> dict:
        """
        為指定租戶建立新班別。
        """
        import uuid
        from datetime import time
        try:
            tenant_id = uuid.UUID(tenant_id_str)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="無效的租戶 ID 格式",
            )

        try:
            # 支援 HH:MM:SS 或 HH:MM
            start_parts = [int(x) for x in start_time_str.split(":")]
            end_parts = [int(x) for x in end_time_str.split(":")]
            
            start_time = time(*start_parts)
            end_time = time(*end_parts)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="時間格式錯誤，請使用 HH:MM 或 HH:MM:SS",
            )

        async with self._session_factory.session() as session:
            new_shift = Shift(
                tenant_id=tenant_id,
                name=name,
                start_time=start_time,
                end_time=end_time,
                geofence_type=geofence_type,
                geofence_data=geofence_data,
            )
            session.add(new_shift)
            await session.commit()
            return {"message": "班別建立成功", "shift_id": str(new_shift.id)}

    async def create_employee(
        self,
        tenant_id_str: str,
        name: str,
        email: str,
        password: str,
    ) -> dict:
        """
        在特定租戶下新增員工。
        """
        import uuid
        try:
            tenant_id = uuid.UUID(tenant_id_str)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="無效的租戶 ID 格式",
            )

        async with self._session_factory.session() as session:
            # 同一租戶下 email 不能重複
            stmt = select(User).where(User.tenant_id == tenant_id, User.email == email)
            result = await session.execute(stmt)
            if result.scalars().first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="該 Email 在此租戶中已被使用",
                )

            hashed_pw = AuthService.get_password_hash(password)
            new_user = User(
                tenant_id=tenant_id,
                email=email,
                name=name,
                role="employee",
                hashed_password=hashed_pw,
            )
            session.add(new_user)
            await session.commit()
            return {"message": "員工帳號建立成功", "employee_id": str(new_user.id)}

