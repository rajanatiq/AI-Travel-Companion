import pytest
from app.engine.scoring import ScoringFormula
from app.engine.crowd_heuristic import estimate_crowd_level

def test_scoring_formula_interest_match():
    poi_food = {
        "category": "food",
        "rating": 4.8,
        "price_tier": 2,
        "visit_duration_min": 60
    }
    poi_other = {
        "category": "shopping",
        "rating": 4.8,
        "price_tier": 2,
        "visit_duration_min": 60
    }
    
    score_food = ScoringFormula.score_place(poi_food, user_interests=["food", "history"], budget_tier=2)
    score_other = ScoringFormula.score_place(poi_other, user_interests=["food", "history"], budget_tier=2)
    
    # Food POI should score significantly higher when user has food interest
    assert score_food > score_other
    assert 0.0 <= score_food <= 1.0

def test_scoring_formula_budget_alignment():
    poi_budget_2 = {"category": "culture", "rating": 4.5, "price_tier": 2, "visit_duration_min": 90}
    poi_budget_4 = {"category": "culture", "rating": 4.5, "price_tier": 4, "visit_duration_min": 90}
    
    # User with budget tier 2 should prefer price tier 2
    score_tier2 = ScoringFormula.score_place(poi_budget_2, user_interests=["culture"], budget_tier=2)
    score_tier4 = ScoringFormula.score_place(poi_budget_4, user_interests=["culture"], budget_tier=2)
    
    assert score_tier2 > score_tier4

def test_crowd_heuristic():
    assert estimate_crowd_level("food", hour=13, is_weekend=False) == "high"
    assert estimate_crowd_level("food", hour=16, is_weekend=False) == "low"
    assert estimate_crowd_level("nightlife", hour=23, is_weekend=True) == "high"
    assert estimate_crowd_level("nature", hour=8, is_weekend=False) == "low"
