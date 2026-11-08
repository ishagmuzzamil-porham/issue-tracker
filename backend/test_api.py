import os

os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_issue_rejects_unknown_type():
    response = client.post(
        "/issues",
        json={
            "title": "Test issue",
            "description": "testing",
            "type": "banana",
            "project_id": 1,
            "reported_by": "Sara",
        },
    )
    assert response.status_code == 422


def test_create_issue_rejects_short_title():
    response = client.post(
        "/issues",
        json={
            "title": "ab",
            "description": "testing",
            "project_id": 1,
            "reported_by": "Sara",
        },
    )
    assert response.status_code == 422