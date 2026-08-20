import pytest
import uuid

def test_itinerary_item_manipulation(client, auth_headers):
    # 1. Create a trip first
    trip_payload = {
        "destination": "Kyoto, Japan",
        "start_date": "2026-11-10",
        "end_date": "2026-11-12",
        "budget_total": 750.0,
        "interests": ["history", "art"],
        "pace": "balanced"
    }
    trip_res = client.post("/api/v1/trips", json=trip_payload, headers=auth_headers)
    assert trip_res.status_code == 201
    trip_data = trip_res.json()
    trip_id = trip_data["id"]

    # 2. Add manual item
    item_payload = {
        "day_index": 0,
        "order_index": 99,
        "place_id": "custom-tea-ceremony",
        "name": "Traditional Japanese Tea Ceremony",
        "category": "culture",
        "scheduled_time": "16:30",
        "duration_min": 60,
        "est_cost": 35.0,
        "crowd_level": "low",
        "notes": "Booked private session"
    }
    add_res = client.post(f"/api/v1/trips/{trip_id}/items", json=item_payload, headers=auth_headers)
    assert add_res.status_code == 201
    item_data = add_res.json()
    assert item_data["name"] == "Traditional Japanese Tea Ceremony"
    assert item_data["user_edited"] is True
    item_id = item_data["id"]

    # 3. Patch / Update item
    patch_payload = {
        "scheduled_time": "17:00",
        "notes": "Rescheduled for 5 PM"
    }
    patch_res = client.patch(f"/api/v1/trips/{trip_id}/items/{item_id}", json=patch_payload, headers=auth_headers)
    assert patch_res.status_code == 200
    assert patch_res.json()["scheduled_time"] == "17:00"
    assert patch_res.json()["notes"] == "Rescheduled for 5 PM"

    # 4. Delete item
    del_res = client.delete(f"/api/v1/trips/{trip_id}/items/{item_id}", headers=auth_headers)
    assert del_res.status_code == 204
