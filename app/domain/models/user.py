"""
app/domain/models/user.py
使用者領域模型。
"""
import uuid
from sqlalchemy import Column, String, Uuid, UniqueConstraint, ForeignKey
from app.infrastructure.database.base import Base, TenantAwareMixin


class User(Base, TenantAwareMixin):
    """
    使用者模型（員工、主管、管理員）。
    P1-2：在 (tenant_id, email) 上加入 UniqueConstraint，確保同一租戶內 Email 不重複。
    P1-3：使用 SQLAlchemy 2.x 原生 Uuid 型別。
    """
    __tablename__ = "users"

    # P1-3：使用原生 Uuid 取代 PostgreSQL 方言特定的 UUID
    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String, nullable=False)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False, default="employee")  # admin, manager, employee
    hashed_password = Column(String, nullable=True)

    # P1-2：確保同一租戶內 Email 唯一，跨租戶允許相同 Email
    __table_args__ = (
        UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
    )
