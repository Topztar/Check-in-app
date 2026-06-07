"""
app/application/admin_service.py
管理員應用服務 — 封裝租戶管理員的登入與註冊業務邏輯。
將資料庫操作從 Presentation 層（router.py）移至 Application 層，
維持清晰的分層架構：Presentation → Application → Domain → Infrastructure。
"""
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.domain.models import Tenant, User
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
