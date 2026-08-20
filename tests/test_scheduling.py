import pytest
from app.engine.scheduling import SchedulingEngine

def test_scheduling_engine_generates_days():
    sample_candidates = [
        {"place_id": f"p{i}", "name": f"Attraction {i}", "category": "history" if i % 2 == 0 else "nature", "rating": 4.7, "price_tier": 2, "visit_duration_min": 90, "est_cost": 20.0, "lat": 48.85, "lon": 2.35}
        for i in range(15)
    ]
    
    days = SchedulingEngine.generate_itinerary(
        destination="Paris, France",
        start_date_str="2026-09-01",
        end_date_str="2026-09-03",
        budget_total=900.0,
        interests=["history", "nature"],
        pace="balanced",
        candidate_places=sample_candidates
    )
    
    # Must generate exactly 3 days (Sept 1, 2, 3)
    assert len(days) == 3
    
    for day in days:
        assert len(day["items"]) >= 3
        # Verify meal presence
        meal_categories = [i["category"] for i in day["items"]]
        assert "food" in meal_categories
        assert day["day_budget_estimate"] > 0
