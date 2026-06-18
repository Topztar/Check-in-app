from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from pathlib import Path

# 獲取專案根目錄中的 templates 資料夾路徑
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

web_router = APIRouter()

@web_router.get("/admin/login")
async def admin_login_page(request: Request):
    """
    渲染管理員登入頁面
    """
    return templates.TemplateResponse(
        request=request, name="admin_login.html"
    )


@web_router.get("/admin/register")
async def admin_register_page(request: Request):
    return templates.TemplateResponse(
        request=request, name="admin_register.html"
    )


@web_router.get("/admin/dashboard")
async def admin_dashboard_page(request: Request):
    return templates.TemplateResponse(
        request=request, name="admin_dashboard.html"
    )


