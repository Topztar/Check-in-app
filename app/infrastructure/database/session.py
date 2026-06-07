"""
app/infrastructure/database/session.py
非同步資料庫 Session 工廠 — 封裝 SQLAlchemy 非同步引擎與 Session 管理。
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


class Database:
    def __init__(self, db_url: str) -> None:
        # P0-5：echo 設定由 settings.debug 控制，正式環境不輸出 SQL 語句
        self._engine = create_async_engine(db_url, echo=settings.debug)
        self._session_factory = sessionmaker(
            self._engine, class_=AsyncSession, expire_on_commit=False,
        )

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """提供一個具有自動 rollback 與 close 的非同步 Session 上下文管理器。"""
        session: AsyncSession = self._session_factory()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
