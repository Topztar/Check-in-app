"""
app/infrastructure/containers.py
依賴注入容器定義 — 使用 dependency-injector 管理服務的生命週期與注入。
P1-1：新增 AdminService 的 Factory 提供者。
"""
from dependency_injector import containers, providers
from app.infrastructure.database.session import Database
from app.infrastructure.services.redis_mock import RedisMockService
from app.infrastructure.services.rekognition_mock import RekognitionMockService
from app.application.admin_service import AdminService


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(packages=["app.presentation"])

    config = providers.Configuration()

    # 資料庫單例 — 整個應用程式共用同一個引擎實例
    db = providers.Singleton(
        Database,
        db_url=config.db.url,
    )

    # Redis 模擬服務（開發/測試環境使用）
    redis_service = providers.Singleton(
        RedisMockService,
    )

    # Rekognition 模擬服務（開發/測試環境使用）
    rekognition_service = providers.Singleton(
        RekognitionMockService,
    )

    # P1-1：管理員應用服務 — 使用 Factory 以便每次請求注入正確的 db 工廠
    admin_service = providers.Factory(
        AdminService,
        session_factory=db,
    )
