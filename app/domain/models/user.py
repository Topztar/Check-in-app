import uuid
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.infrastructure.database.base import Base, TenantAwareMixin

class User(Base, TenantAwareMixin):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String, nullable=False)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False, default="employee") # admin, manager, employee
