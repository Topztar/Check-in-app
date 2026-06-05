import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "服務運作正常"}

def test_enroll_device():
    payload = {
        "user_id": "test-user-id",
        "device_name": "Test iPhone",
        "public_key_pem": "mock-pem"
    }
    response = client.post("/api/v1/auth/device/enroll", json=payload)
    assert response.status_code == 200
    assert response.json()["message"] == "設備註冊成功"
    assert "device_id" in response.json()

def test_get_challenge():
    payload = {"device_id": "mock-device-id"}
    response = client.post("/api/v1/auth/challenge", json=payload)
    assert response.status_code == 200
    assert response.json()["message"] == "挑戰碼產生成功"
    assert "challenge" in response.json()

def test_biometric_login():
    # First get a challenge
    challenge_response = client.post("/api/v1/auth/challenge", json={"device_id": "mock-device-id"})
    
    payload = {
        "device_id": "mock-device-id",
        "signature_b64": "mock-signature"
    }
    response = client.post("/api/v1/auth/biometric/login", json=payload)
    assert response.status_code == 200
    assert response.json()["message"] == "登入成功"
    assert "token" in response.json()

def test_clock_in():
    # Get a challenge first
    challenge_response = client.post("/api/v1/auth/challenge", json={"device_id": "mock-device-id"})
    
    import base64
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
    assert response.status_code == 200
    assert response.json()["message"] == "打卡成功"
    assert "smoothed_location" in response.json()
    assert "liveness_session_id" in response.json()

def test_admin_register():
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
    # Attempt login with the newly created user
    payload = {
        "username": "testadmin@company.com",
        "password": "securepassword123"
    }
    response = client.post("/api/v1/admin/login", json=payload)
    assert response.status_code == 200
    assert response.json()["message"] == "登入成功"
    assert "token" in response.json()
