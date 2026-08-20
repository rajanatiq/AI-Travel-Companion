import pytest
import uuid

def test_expense_logging_and_budget_summary(client, auth_headers):
    # 1. Create a trip first
    trip_payload = {
        "destination": "Rome, Italy",
        "start_date": "2026-11-01",
        "end_date": "2026-11-04",
        "budget_total": 800.0,
        "interests": ["history", "food"],
        "pace": "relaxed"
    }
    trip_res = client.post("/api/v1/trips", json=trip_payload, headers=auth_headers)
    trip_id = trip_res.json()["id"]

    # 2. Log single expense
    exp_payload = {
        "category": "meals",
        "amount": 45.50,
        "currency": "USD",
        "note": "Pasta & Wine in Trastevere"
    }
    res_exp = client.post(f"/api/v1/trips/{trip_id}/expenses", json=exp_payload, headers=auth_headers)
    assert res_exp.status_code == 201
    assert res_exp.json()["amount"] == 45.50

    # 3. Batch offline sync
    offline_payload = {
        "expenses": [
            {"id": str(uuid.uuid4()), "category": "transport", "amount": 15.0, "currency": "USD", "note": "Metro pass", "logged_at": "2026-11-01T10:00:00Z"},
            {"id": str(uuid.uuid4()), "category": "activity", "amount": 30.0, "currency": "USD", "note": "Colosseum ticket", "logged_at": "2026-11-01T14:00:00Z"}
        ]
    }
    res_sync = client.post(f"/api/v1/trips/{trip_id}/expenses/sync", json=offline_payload, headers=auth_headers)
    assert res_sync.status_code == 200
    assert res_sync.json()["synced_count"] == 2

    # 4. Check Budget Summary
    res_budget = client.get(f"/api/v1/trips/{trip_id}/expenses/budget/summary", headers=auth_headers)
    assert res_budget.status_code == 200
    budget_info = res_budget.json()
    assert budget_info["budget_total"] == 800.0
    assert budget_info["spent"] == round(45.50 + 15.0 + 30.0, 2)
    assert budget_info["remaining"] == round(800.0 - (45.50 + 15.0 + 30.0), 2)
    assert "meals" in budget_info["category_breakdown"]
