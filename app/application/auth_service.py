"""
app/application/auth_service.py
認證應用服務 — 負責密碼雜湊、JWT 產生與 ECDSA 簽章驗證。
所有設定值均從 app.core.config.settings 取得，不得寫死在程式碼中。
"""
from ecdsa import VerifyingKey, BadSignatureError
import base64
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta, timezone

from app.core.config import settings

# 密碼雜湊配置（使用 bcrypt）
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    @staticmethod
    def verify_signature(public_key_pem: str, signature_b64: str, message: str) -> bool:
        """
        驗證 ECDSA secp256r1 簽章。
        :param public_key_pem: 裝置公鑰（PEM 格式）
        :param signature_b64:  Base64 編碼的簽章
        :param message:        原始挑戰碼字串
        :return: 驗證成功為 True，否則為 False
        """
        try:
            vk = VerifyingKey.from_pem(public_key_pem)
            signature = base64.b64decode(signature_b64)
            # vk.verify 回傳 True 或拋出 BadSignatureError
            vk.verify(signature, message.encode('utf-8'))
            return True
        except (BadSignatureError, ValueError, TypeError):
            return False

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """驗證明文密碼與雜湊值是否相符。"""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        """將明文密碼雜湊化後回傳。"""
        return pwd_context.hash(password)

    @staticmethod
    def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
        """
        產生 JWT Access Token。
        :param data:          要編碼進 Token 的 Payload 資料
        :param expires_delta: 自訂過期時間；若未指定，使用 settings.access_token_expire_minutes
        :return: 已簽名的 JWT 字串
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            # 使用設定檔中的過期分鐘數，不再寫死 15 分鐘
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=settings.access_token_expire_minutes
            )
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(
            to_encode,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        return encoded_jwt
