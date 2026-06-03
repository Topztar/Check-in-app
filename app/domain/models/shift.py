import uuid
from sqlalchemy import Column, String, Time, Date, ForeignKeyConstraint, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.infrastructure.database.base import Base, TenantAwareMixin

class Shift(Base, TenantAwareMixin):
    __tablename__ = "shifts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    # GeoFence configuration (can be circle or polygon)
    geofence_type = Column(String, nullable=False) # "circle" or "polygon"
    geofence_data = Column(JSONB, nullable=False) # {"lat": ..., "lng": ..., "radius": ...} or [{"lat": ..., "lng": ...}, ...]
