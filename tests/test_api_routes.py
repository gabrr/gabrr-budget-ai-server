from fastapi.testclient import TestClient

from app.main import app
from app.mock_data import store

client = TestClient(app)


def setup_function() -> None:
    store.reset()


def test_list_categories_returns_seeded_data() -> None:
    response = client.get("/categories")

    assert response.status_code == 200
    data = response.json()
    assert any(category["key"] == "food" for category in data)
    assert any(category["key"] == "others" for category in data)


def test_transactions_support_filters_and_pagination() -> None:
    response = client.get(
        "/transactions",
        params={
            "category": "food",
            "date_from": "2026-04-01",
            "date_to": "2026-04-30",
            "limit": 2,
            "offset": 0,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["limit"] == 2
    assert payload["offset"] == 0
    assert payload["total"] >= 1
    assert len(payload["items"]) <= 2
    assert all(item["category"] == "food" for item in payload["items"])


def test_get_transaction_by_id_returns_seeded_record() -> None:
    response = client.get("/transactions/8")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == "8"
    assert payload["category"] == "others"


def test_patch_transaction_updates_category() -> None:
    response = client.patch("/transactions/8", json={"category": "needs"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == "8"
    assert payload["category"] == "needs"

    persisted = client.get("/transactions/8")
    assert persisted.status_code == 200
    assert persisted.json()["category"] == "needs"


def test_bulk_create_transactions_persists_imported_rows() -> None:
    response = client.post(
        "/transactions/bulk",
        json={
            "transactions": [
                {
                    "description": "Imported Coffee",
                    "amount": 5.4,
                    "date": "2026-04-24",
                    "category": "food",
                    "merchant": "Starbucks",
                },
                {
                    "description": "Imported Review Item",
                    "amount": 45.2,
                    "date": "2026-04-23",
                    "category": "others",
                    "merchant": "Target",
                },
            ]
        },
    )

    assert response.status_code == 201
    created = response.json()
    assert len(created) == 2
    created_id = created[1]["id"]

    persisted = client.get(f"/transactions/{created_id}")
    assert persisted.status_code == 200
    assert persisted.json()["merchant"] == "Target"
