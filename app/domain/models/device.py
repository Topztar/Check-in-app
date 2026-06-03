import uuid
from sqlalchemy import Column, String, ForeignKey, ForeignKeyConstraint
from sqlalchemy.dialects.postgresql import UUID
from app.infrastructure.database.base import Base, TenantAwareMixin
from app.domain.models.user import User

class Device(Base, TenantAwareMixin):
    __tablename__ = "devices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    device_name = Column(String, nullable=False)
    public_key = Column(String, nullable=False) # ecdsa secp256r1 public key
    
    __table_args__ = (
        ForeignKeyConstraint(
            ['tenant_id', 'user_id'],
            ['users.tenant_id', 'users.id'],
            ondelete="CASCADE"
        ),
    )
