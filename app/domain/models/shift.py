"""
app/domain/models/shift.py
班別領域模型。
"""
import uuid
from sqlalchemy import Column, String, Time, Uuid, JSON
from app.infrastructure.database.base import Base, TenantAwareMixin


class Shift(Base, TenantAwareMixin):
    """
    班別模型 — 定義工作時間與地理圍欄設定。
    P1-3：使用 SQLAlchemy 2.x 原生 Uuid 型別。
    geofence_data 結構：
      - 圓形（geofence_type="circle"）：{"lat": float, "lng": float, "radius": float (公尺)}
      - 多邊形（geofence_type="polygon"）：[{"lat": float, "lng": float}, ...]
    """
    __tablename__ = "shifts"

    # P1-3：使用原生 Uuid 取代 PostgreSQL 方言特定的 UUID
    id = Column(Uuid, primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    # 地理圍欄型態：「circle」或「polygon」
    geofence_type = Column(String, nullable=False)
    # 地理圍欄資料（JSON）
    geofence_data = Column(JSON, nullable=False)
