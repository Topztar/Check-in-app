"""
app/domain/models/tenant.py
租戶領域模型。
"""
import uuid
from sqlalchemy import Column, String, Uuid
from app.infrastructure.database.base import Base


class Tenant(Base):
    """
    租戶（企業客戶）模型。
    每個租戶代表一個使用本系統的企業客戶。
    P1-3：使用 SQLAlchemy 2.x 原生 Uuid 型別。
    """
    __tablename__ = "tenants"

    # P1-3：使用原生 Uuid 取代 PostgreSQL 方言特定的 UUID
    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=False)
