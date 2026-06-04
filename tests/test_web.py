import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_admin_login_page():
    response = client.get("/admin/login")
    assert response.status_code == 200
    assert "管理員登入" in response.text

def test_static_files():
    response = client.get("/static/style.css")
    assert response.status_code == 200
    assert "body" in response.text
    
    response = client.get("/static/app.js")
    assert response.status_code == 200
    assert "document.getElementById" in response.text
