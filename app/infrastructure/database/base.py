import uuid
from typing import Any

from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, declared_attr
from sqlalchemy.sql.schema import MetaData

# Ensure all tables have a naming convention
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
metadata = MetaData(naming_convention=convention)

class BaseMixin:
    """Base class for all SQLAlchemy Models."""
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()
        
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

Base = declarative_base(cls=BaseMixin, metadata=metadata)

class TenantAwareMixin:
    """Mixin to add tenant_id to models, creating composite primary keys where applicable."""
    tenant_id = Column(UUID(as_uuid=True), primary_key=True, index=True, nullable=False)

