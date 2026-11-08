"""Smoke test for application health check endpoint."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "MavChat is running" in data["message"]


def test_landing_page_redirect():
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 200

