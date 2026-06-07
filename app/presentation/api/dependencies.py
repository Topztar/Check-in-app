"""
app/presentation/api/dependencies.py
FastAPI 依賴注入函式 — 提供 JWT 認證保護的依賴項目。
"""
from typing import Any
import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.config import settings

# HTTP Bearer Token 提取器
_bearer_scheme = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> dict[str, Any]:
    """
    從 Authorization: Bearer <token> 標頭解碼 JWT，回傳 payload 資料。
    若 Token 無效或已過期，拋出 401 Unauthorized。
    """
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="無效或已過期的 Token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 已過期",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise credentials_exception


def get_db(request: Request):
    """從 DI 容器取得資料庫工廠。"""
    return request.app.container.db()


def get_redis_service(request: Request):
    """從 DI 容器取得 Redis（Mock）服務。"""
    return request.app.container.redis_service()


def get_rekognition_service(request: Request):
    """從 DI 容器取得 Rekognition（Mock）服務。"""
    return request.app.container.rekognition_service()
