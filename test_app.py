"""Kiểm thử tự động cho app.py - Jenkins chạy file này ở stage Test."""
import pytest

from app import app, add


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_add():
    assert add(2, 3) == 5


def test_index(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "version" in res.get_json()


def test_health(client):
    res = client.get("/health")
    assert res.get_json() == {"status": "ok"}


def test_api_sum(client):
    res = client.get("/api/sum?a=4&b=6")
    assert res.status_code == 200
    assert res.get_json()["result"] == 10


def test_api_sum_invalid(client):
    res = client.get("/api/sum?a=abc&b=1")
    assert res.status_code == 400


# ===== KỊCH BẢN DEMO 2: PIPELINE THẤT BẠI =====
# Bỏ dấu # ở 2 dòng dưới rồi push lên GitHub.
# Stage Test sẽ báo đỏ, pipeline dừng lại và KHÔNG triển khai.
# def test_demo_fail():
#     assert add(2, 2) == 5
