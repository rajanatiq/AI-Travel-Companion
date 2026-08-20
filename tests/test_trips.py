import pytest
import uuid

def test_create_and_get_trip_flow(client, auth_headers):
    trip_payload = {
        "destination": "Tokyo, Japan",
        "start_date": "2026-10-10",
        "end_date": "2026-10-12",
        "budget_total": 1200.0,
        "interests": ["food", "history", "art"],
        "pace": "balanced"
    }
    
    # 1. Create Trip (triggers AI Engine)
    res_create = client.post("/api/v1/trips", json=trip_payload, headers=auth_headers)
    assert res_create.status_code == 201
    trip_data = res_create.json()
    
    assert trip_data["destination"] == "Tokyo, Japan"
    assert len(trip_data["days"]) == 3
    assert trip_data["total_activities"] > 0
    trip_id = trip_data["id"]

    # 2. Get Trip By ID
    res_get = client.get(f"/api/v1/trips/{trip_id}", headers=auth_headers)
    assert res_get.status_code == 200
    assert res_get.json()["id"] == trip_id

    # 3. List Trips
    res_list = client.get("/api/v1/trips", headers=auth_headers)
    assert res_list.status_code == 200
    assert len(res_list.json()) >= 1

    # 4. Patch Trip
    res_patch = client.patch(f"/api/v1/trips/{trip_id}", json={"status": "completed"}, headers=auth_headers)
    assert res_patch.status_code == 200
    assert res_patch.json()["status"] == "completed"

    # 5. Delete Trip
    res_del = client.delete(f"/api/v1/trips/{trip_id}", headers=auth_headers)
    assert res_del.status_code == 204
