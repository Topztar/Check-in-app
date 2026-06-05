from ecdsa import VerifyingKey, BadSignatureError
import base64
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta, timezone

# 密碼雜湊配置
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT 配置 (在正式環境應從環境變數取得)
SECRET_KEY = "super-secret-key-for-jwt"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

class AuthService:
    @staticmethod
    def verify_signature(public_key_pem: str, signature_b64: str, message: str) -> bool:
        """
        Verify an ECDSA secp256r1 signature.
        """
        try:
            vk = VerifyingKey.from_pem(public_key_pem)
            signature = base64.b64decode(signature_b64)
            return vk.verify(signature, message.encode('utf-8'))
        except (BadSignatureError, ValueError, TypeError):
            return False

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
