import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# 1. 初始化 DI 容器並設定 Wiring (依賴注入綁定)
from app.infrastructure.containers import Container
container = Container()
container.wire(packages=["app.presentation"])

# 2. 引入 API Router 與 Web Router
from app.presentation.api.router import api_router
from app.presentation.web_router import web_router

def create_app() -> FastAPI:
    app = FastAPI(
        title="Enterprise Multi-Tenant Employee Attendance SaaS",
        description="Backend API for attendance tracking with biometric and geofencing capabilities.",
        version="1.0.0"
    )
    
    # 加入 CORS Middleware 以允許前端通訊
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "https://attendance-saas-api.onrender.com"], # 允許來源 (包含本地端 React 預設 port)
        allow_credentials=True, # 允許傳送 Cookie (例如 HttpOnly token)
        allow_methods=["*"], # 允許所有 HTTP 方法 (GET, POST, PUT, DELETE, OPTIONS等)
        allow_headers=["*"], # 允許所有 Header (包含 Authorization)
    )
    
    app.container = container

    @app.get("/health", summary="Health Check")
    async def health_check():
        return JSONResponse(content={"status": "ok", "message": "服務運作正常"})
        
    # 掛載靜態檔案 (Static Files)
    # 將 /static 路徑映射到 app/presentation/static 資料夾
    BASE_DIR = Path(__file__).resolve().parent
    app.mount("/static", StaticFiles(directory=str(BASE_DIR / "presentation" / "static")), name="static")
    
    # 註冊 API 路由 (前綴為 /api/v1)
    app.include_router(api_router, prefix="/api/v1")
    
    # 註冊 Web 頁面路由 (無特定前綴，或您也可以加上 /admin 前綴)
    app.include_router(web_router)

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
