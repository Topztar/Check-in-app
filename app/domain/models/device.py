"""
app/domain/models/device.py
裝置領域模型 — 儲存使用者的已認證裝置及其 ECDSA 公鑰。
"""
import uuid
from sqlalchemy import Column, String, Uuid, ForeignKeyConstraint
from app.infrastructure.database.base import Base, TenantAwareMixin


class Device(Base, TenantAwareMixin):
    """
    裝置模型 — 每筆記錄對應一個已完成生物辨識裝置註冊的行動設備。
    P1-3：使用 SQLAlchemy 2.x 原生 Uuid 型別。
    """
    __tablename__ = "devices"

    # P1-3：使用原生 Uuid 取代 PostgreSQL 方言特定的 UUID
    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(Uuid, nullable=False)
    device_name = Column(String, nullable=False)
    # ECDSA secp256r1 公鑰（PEM 格式）
    public_key = Column(String, nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "user_id"],
            ["users.tenant_id", "users.id"],
            ondelete="CASCADE",
        ),
    )
