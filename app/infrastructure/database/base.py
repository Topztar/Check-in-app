"""
app/infrastructure/database/base.py
SQLAlchemy 宣告式基底類別與共用 Mixin。
使用 SQLAlchemy 2.x 原生 Uuid 型別，相容 PostgreSQL 與 SQLite。
"""
import uuid
from typing import Any

from sqlalchemy import Column, DateTime, Uuid, func
from sqlalchemy.orm import declarative_base, declared_attr
from sqlalchemy.sql.schema import MetaData

# 確保所有約束均有統一命名規則，方便 Alembic 遷移管理
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
metadata = MetaData(naming_convention=convention)


class BaseMixin:
    """所有 SQLAlchemy 模型的基底 Mixin，提供自動 tablename 與時間戳記欄位。"""
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


Base = declarative_base(cls=BaseMixin, metadata=metadata)


class TenantAwareMixin:
    """
    租戶感知 Mixin — 為模型增加 tenant_id 主鍵，形成複合主鍵以支援多租戶隔離。
    P1-3：改用 SQLAlchemy 2.x 原生 Uuid 型別（取代 PostgreSQL 方言特定的 UUID）。
    """
    # P1-3：使用 sqlalchemy.Uuid（SQLAlchemy 2.x 原生型別，PostgreSQL 與 SQLite 均相容）
    tenant_id = Column(Uuid, primary_key=True, index=True, nullable=False)
