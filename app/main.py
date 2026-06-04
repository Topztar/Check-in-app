import sys
from fastapi import FastAPI
from fastapi.responses import JSONResponse

# 1. 初始化 DI 容器並設定 Wiring (依賴注入綁定)
from app.infrastructure.containers import Container
container = Container()
container.wire(packages=["app.presentation"])

# 2. 引入 Router (確保在此之前容器已經 wired)
from app.presentation.api.router import api_router

def create_app() -> FastAPI:
    app = FastAPI(
        title="Enterprise Multi-Tenant Employee Attendance SaaS",
        description="Backend API for attendance tracking with biometric and geofencing capabilities.",
        version="1.0.0"
    )
    
    app.container = container

    @app.get("/health", summary="Health Check")
    async def health_check():
        return JSONResponse(content={"status": "ok", "message": "服務運作正常"})
        
    app.include_router(api_router, prefix="/api/v1")

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
