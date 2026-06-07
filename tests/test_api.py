"""
tests/test_api.py
API 整合測試 — 測試所有 API 端點的基本功能。
部分端點現在需要 JWT 認證，測試中使用真實流程或模擬 token。
"""
import pytest
import base64
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "服務運作正常"}


def test_get_challenge():
    """挑戰碼端點不需要認證，任何裝置都可以取得挑戰碼。"""
    payload = {"device_id": "mock-device-id"}
    response = client.post("/api/v1/auth/challenge", json=payload)
    assert response.status_code == 200
    assert response.json()["message"] == "挑戰碼產生成功"
    assert "challenge" in response.json()


def test_enroll_device_requires_auth():
    """設備註冊端點現在需要 JWT 認證，未帶 token 應回傳 403/401。"""
    payload = {
        "user_id": "test-user-id",
        "device_name": "Test iPhone",
        "public_key_pem": "mock-pem"
    }
    response = client.post("/api/v1/auth/device/enroll", json=payload)
    # 無 JWT token 應被拒絕
    assert response.status_code in (401, 403, 422)


def test_biometric_login_no_challenge():
    """若未先取得挑戰碼，生物辨識登入應回傳 401。"""
    payload = {
        "device_id": "nonexistent-device-id",
        "signature_b64": "mock-signature"
    }
    response = client.post("/api/v1/auth/biometric/login", json=payload)
    assert response.status_code == 401
    assert "挑戰碼已過期或無效" in response.json()["detail"]


def test_admin_register():
    """管理員註冊應成功建立租戶與使用者。"""
    payload = {
        "tenant_name": "Test Company",
        "admin_name": "Test Admin",
        "email": "testadmin@company.com",
        "password": "securepassword123"
    }
    response = client.post("/api/v1/admin/register", json=payload)
    assert response.status_code == 200
    assert response.json()["message"] == "註冊成功，請導向登入頁面"


def test_admin_login():
    """使用已建立的帳號登入，應取得 JWT Token。"""
    payload = {
        "username": "testadmin@company.com",
        "password": "securepassword123"
    }
    response = client.post("/api/v1/admin/login", json=payload)
    assert response.status_code == 200
    assert response.json()["message"] == "登入成功"
    assert "token" in response.json()


def test_admin_login_wrong_password():
    """密碼錯誤應回傳 401。"""
    payload = {
        "username": "testadmin@company.com",
        "password": "wrongpassword"
    }
    response = client.post("/api/v1/admin/login", json=payload)
    assert response.status_code == 401


def test_admin_register_duplicate_email():
    """重複的 Email 應回傳 400。"""
    payload = {
        "tenant_name": "Another Company",
        "admin_name": "Another Admin",
        "email": "testadmin@company.com",  # 已存在的 email
        "password": "anotherpassword"
    }
    response = client.post("/api/v1/admin/register", json=payload)
    assert response.status_code == 400
    assert "已被註冊" in response.json()["detail"]


def test_clock_in_requires_auth():
    """打卡端點需要 JWT 認證，未帶 token 應被拒絕。"""
    mock_image = base64.b64encode(b"mock_image_data").decode("utf-8")
    payload = {
        "user_id": "test-user",
        "shift_id": "test-shift",
        "device_id": "mock-device-id",
        "signature_b64": "mock-signature",
        "gps_coordinates": [
            {"lat": 0.0001, "lon": 0.0001},
            {"lat": 0.0002, "lon": 0.0002}
        ],
        "image_bytes_b64": mock_image
    }
    response = client.post("/api/v1/attendance/clock-in", json=payload)
    # 無 JWT token 應被拒絕
    assert response.status_code in (401, 403, 422)
