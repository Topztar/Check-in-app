"""
app/infrastructure/services/redis_mock.py
Redis 模擬服務 — 在開發/測試環境中取代真實 Redis，支援 TTL 過期機制。
P2-6：加入時間戳記追蹤，實現基於 TTL 的自動過期。
"""
import uuid
import time
from typing import Optional


class RedisMockService:
    """
    記憶體內 Redis 模擬服務。
    - 儲存挑戰碼時記錄建立時間
    - 讀取挑戰碼時檢查是否已超過 TTL
    - 超過 TTL 的挑戰碼視為無效並自動移除

    P2-6：使用 time.monotonic() 追蹤建立時間以實現 TTL 過期。
    """

    def __init__(self) -> None:
        # 儲存格式：{device_id: (challenge, created_at_monotonic)}
        self._store: dict[str, tuple[str, float]] = {}

    async def set_challenge(self, device_id: str, ttl: int = 60) -> str:
        """
        為指定裝置設定一個新的挑戰碼。
        :param device_id: 裝置唯一識別碼
        :param ttl:       過期時間（秒），預設 60 秒
        :return: 產生的挑戰碼（UUID 字串）
        """
        challenge = str(uuid.uuid4())
        # 記錄建立時間以供後續 TTL 檢查
        self._store[device_id] = (challenge, time.monotonic(), ttl)
        return challenge

    async def get_challenge(self, device_id: str) -> Optional[str]:
        """
        取得裝置的挑戰碼。
        P2-6：若挑戰碼已超過 TTL，自動移除並回傳 None。
        :param device_id: 裝置唯一識別碼
        :return: 有效的挑戰碼，或 None（不存在/已過期）
        """
        entry = self._store.get(device_id)
        if entry is None:
            return None

        challenge, created_at, ttl = entry
        elapsed = time.monotonic() - created_at

        if elapsed > ttl:
            # 挑戰碼已過期，從記憶體中移除
            del self._store[device_id]
            return None

        return challenge

    async def delete_challenge(self, device_id: str) -> None:
        """明確移除已使用的挑戰碼（防止重放攻擊）。"""
        self._store.pop(device_id, None)
