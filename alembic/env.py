"""
alembic/env.py
Alembic 遷移環境設定 — 從 settings 取得資料庫 URL，不從 alembic.ini 寫死。
"""
import asyncio
import os
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

from app.infrastructure.database.base import Base
from app.domain.models import Tenant, User, Device, Shift, AttendanceRecord

# A-1：從 settings 取得資料庫 URL（優先使用環境變數 DB_URL）
from app.core.config import settings

# Alembic Config 物件
config = context.config

# 設定 logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 目標 Metadata（用於 autogenerate 比對）
target_metadata = Base.metadata


def include_name(name, type_, parent_names):
    if type_ == "schema":
        return False
    return True


# A-1：動態覆蓋 alembic.ini 中的 sqlalchemy.url，優先使用環境變數
# 這樣 alembic upgrade head 在 CI/CD 環境中可以正確讀取資料庫 URL
config.set_main_option("sqlalchemy.url", settings.db_url)


def run_migrations_offline() -> None:
    """在「離線」模式下執行遷移（不需要實際資料庫連線）。"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_name=include_name,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_name=include_name,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """在「線上」模式下建立非同步引擎並執行遷移。"""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """在「線上」模式下執行遷移。"""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
