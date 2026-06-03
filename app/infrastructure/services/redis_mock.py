import uuid
import asyncio

class RedisMockService:
    def __init__(self):
        self._store = {}
        
    async def set_challenge(self, device_id: str, ttl: int = 60) -> str:
        challenge = str(uuid.uuid4())
        self._store[device_id] = challenge
        # Simulate TTL expiration (for tests, we might keep it simple)
        asyncio.create_task(self._expire_key(device_id, ttl))
        return challenge
        
    async def get_challenge(self, device_id: str) -> str | None:
        return self._store.get(device_id)
        
    async def _expire_key(self, key: str, delay: int):
        await asyncio.sleep(delay)
        self._store.pop(key, None)
