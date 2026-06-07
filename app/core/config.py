"""
app/core/config.py
應用程式設定管理模組 — 使用 pydantic-settings 從環境變數讀取所有設定值。
所有敏感資訊（如 JWT 金鑰、資料庫 URL）均不得寫死在程式碼中。
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    應用程式全域設定。
    優先順序：環境變數 > .env 檔案 > 預設值。
    生產環境必須透過環境變數覆蓋所有預設值。
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- 資料庫設定 ---
    # 開發環境預設使用 SQLite；正式環境必須設定 PostgreSQL URL
    db_url: str = "sqlite+aiosqlite:///./test.db"

    # --- JWT 安全設定 ---
    # 警告：正式環境必須使用強隨機金鑰，例如：
    #   openssl rand -hex 32
    jwt_secret_key: str = "CHANGE-ME-IN-PRODUCTION-USE-OPENSSL-RAND-HEX-32"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    # --- 除錯設定 ---
    # 正式環境必須設定為 False，避免 SQL 語句洩漏至日誌
    debug: bool = False


@lru_cache()
def get_settings() -> Settings:
    """
    取得應用程式設定單例（透過 lru_cache 快取）。
    在測試中可透過清除快取來替換設定。
    """
    return Settings()


# 模組層級的設定單例，供其他模組直接 import 使用
settings: Settings = get_settings()
