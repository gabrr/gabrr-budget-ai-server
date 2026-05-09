"""Integration tests: require DATABASE_URL (e.g. gabrr_budget_dev via `make dev`)."""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

pytestmark = pytest.mark.skipif(
    not os.environ.get("DATABASE_URL"),
    reason="DATABASE_URL not set",
)


@pytest.fixture
def client() -> TestClient:
    # Import app after env is present (make dev exports DATABASE_URL first)
    from app.main import app

    return TestClient(app)


def test_db_engine_connects() -> None:
    from app.db.session import engine

    with engine.connect() as conn:
        assert conn.execute(text("SELECT 1")).scalar() == 1


def test_list_transactions(client: TestClient) -> None:
    r = client.get("/transactions", params={"limit": 5, "offset": 0})
    assert r.status_code == 200
    body = r.json()
    assert "items" in body and "total" in body
    assert isinstance(body["items"], list)


def test_post_transaction(client: TestClient) -> None:
    r = client.post(
        "/transactions",
        json={
            "posted_at": "2026-05-01",
            "description": "pytest create",
            "amount": "10.00",
        },
    )
    assert r.status_code == 201
    data = r.json()
    assert data.get("id")
    assert data.get("description") == "pytest create"
