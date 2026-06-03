from dependency_injector import containers, providers
from app.infrastructure.database.session import Database
from app.infrastructure.services.redis_mock import RedisMockService
from app.infrastructure.services.rekognition_mock import RekognitionMockService

class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(packages=["app.presentation"])
    
    config = providers.Configuration()
    
    db = providers.Singleton(
        Database,
        db_url=config.db.url,
    )
    
    redis_service = providers.Singleton(
        RedisMockService,
    )
    
    rekognition_service = providers.Singleton(
        RekognitionMockService,
    )
