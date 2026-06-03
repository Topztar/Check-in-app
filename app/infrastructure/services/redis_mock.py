import uuid
import asyncio

class RedisMockService:
    def __init__(self):
        self._store = {}
        
    async def set_challenge(self, device_id: str, ttl: int = 60) -> str:
        challenge = str(uuid.uuid4())
        self._store[device_id] = challenge
        return challenge
        
    async def get_challenge(self, device_id: str) -> str | None:
        # Avoid popping/expiring in tests since TestClient handles concurrency differently
        return self._store.get(device_id)
