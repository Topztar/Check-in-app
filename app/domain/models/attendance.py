"""
app/domain/models/attendance.py
考勤記錄領域模型。
"""
import uuid
from sqlalchemy import Column, String, DateTime, Uuid, Float, ForeignKeyConstraint
from app.infrastructure.database.base import Base, TenantAwareMixin


class AttendanceRecord(Base, TenantAwareMixin):
    """
    考勤打卡記錄模型。
    P1-3：使用 SQLAlchemy 2.x 原生 Uuid 型別。
    P2-3：新增 status 與 clock_in_type 欄位以支援更精細的出勤管理。
    """
    __tablename__ = "attendance_records"

    # P1-3：使用原生 Uuid 取代 PostgreSQL 方言特定的 UUID
    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(Uuid, nullable=False)
    shift_id = Column(Uuid, nullable=False)
    clock_in_time = Column(DateTime(timezone=True), nullable=False)
    clock_out_time = Column(DateTime(timezone=True), nullable=True)

    # 平滑化後的 GPS 座標（卡爾曼濾波處理後）
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    # 活體檢測 Session ID
    liveness_session_id = Column(String, nullable=True)

    # P2-3：出勤狀態欄位
    # 可能值："present"（正常）、"late"（遲到）、"early_leave"（早退）
    status = Column(String, nullable=False, default="present")

    # P2-3：打卡方式欄位
    # 可能值："normal"（正常打卡）、"manual"（手動補打）、"override"（主管覆蓋）
    clock_in_type = Column(String, nullable=False, default="normal")

    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "user_id"],
            ["users.tenant_id", "users.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "shift_id"],
            ["shifts.tenant_id", "shifts.id"],
            ondelete="CASCADE",
        ),
    )
