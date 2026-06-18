import asyncio
import os
import pytest
from sqlalchemy.ext.asyncio import create_async_engine

# 1. 覆蓋 settings.db_url 必須在匯入任何 app 模組之前執行，
# 這樣 app/main.py 匯入時才會使用測試用資料庫。
from app.core.config import settings
TEST_DB_URL = "sqlite+aiosqlite:///./test_temp.db"
settings.db_url = TEST_DB_URL

from app.infrastructure.database.base import Base
from app.domain.models import Tenant, User, Device, Shift, AttendanceRecord

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    db_file = "./test_temp.db"
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
        except OSError:
            pass

    # 建立一個事件迴圈來同步執行非同步的 Table 建立
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    engine = create_async_engine(TEST_DB_URL)
    
    async def create_tables():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
    loop.run_until_complete(create_tables())
    loop.run_until_complete(engine.dispose())
    loop.close()

    yield

    # 清理測試用資料庫
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
        except OSError:
            pass
