import uuid
from sqlalchemy import Column, String, DateTime, ForeignKeyConstraint, Float
from sqlalchemy.dialects.postgresql import UUID
from app.infrastructure.database.base import Base, TenantAwareMixin

class AttendanceRecord(Base, TenantAwareMixin):
    __tablename__ = "attendance_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    shift_id = Column(UUID(as_uuid=True), nullable=False)
    clock_in_time = Column(DateTime(timezone=True), nullable=False)
    clock_out_time = Column(DateTime(timezone=True), nullable=True)
    
    # Store smoothed coordinates
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    # Liveness check passed
    liveness_session_id = Column(String, nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ['tenant_id', 'user_id'],
            ['users.tenant_id', 'users.id'],
            ondelete="CASCADE"
        ),
        ForeignKeyConstraint(
            ['tenant_id', 'shift_id'],
            ['shifts.tenant_id', 'shifts.id'],
            ondelete="CASCADE"
        ),
    )
