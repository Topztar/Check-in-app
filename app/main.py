"""
app/main.py
FastAPI 應用程式進入點 — 負責建立 App 實例、掛載路由與 Middleware。
"""
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# 從設定模組取得設定（P0-4：DB URL 來自環境變數）
from app.core.config import settings

# 1. 初始化 DI 容器並設定 Wiring (依賴注入綁定)
from app.infrastructure.containers import Container
container = Container()
# P0-4：使用 settings.db_url 取代寫死的 SQLite 路徑
container.config.db.url.from_value(settings.db_url)
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

    # P1-5：收緊 CORS 設定，明確列出允許的方法與 Header
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "https://attendance-saas-api.onrender.com"],
        allow_credentials=True,
        # 明確列出允許的 HTTP 方法，不使用萬用字元
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        # 明確列出允許的 Header，不使用萬用字元
        allow_headers=["Authorization", "Content-Type", "Accept"],
    )

    app.container = container

    # --- 處理 Root URL ---
    @app.get("/", include_in_schema=False)
    async def root():
        # 自動導向至後台登入頁面
        return RedirectResponse(url="/admin/login")

    @app.get("/health", summary="Health Check")
    async def health_check():
        return JSONResponse(content={"status": "ok", "message": "服務運作正常"})

    # 掛載靜態檔案
    BASE_DIR = Path(__file__).resolve().parent
    app.mount("/static", StaticFiles(directory=str(BASE_DIR / "presentation" / "static")), name="static")

    # 註冊路由
    app.include_router(api_router, prefix="/api/v1")
    app.include_router(web_router)

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
