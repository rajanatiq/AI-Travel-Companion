"""
Multi-factor POI scoring formula.
Calculates a relevance score between 0.0 and 1.0 for each POI candidate.
"""
from typing import List, Dict, Any

class ScoringFormula:
    # Weights for scoring factors
    W_INTEREST: float = 0.40   # Category match with user interests
    W_RATING: float = 0.25     # Google / curated rating (1.0 to 5.0)
    W_BUDGET: float = 0.20     # Alignment with user budget tier
    W_DIVERSITY: float = 0.15  # Pace & duration compatibility

    @classmethod
    def score_place(
        cls,
        place: Dict[str, Any],
        user_interests: List[str],
        pace: str = "balanced",
        budget_tier: int = 2
    ) -> float:
        """
        Calculate candidate score.
        place dictionary expected to contain: category, rating, price_tier, visit_duration_min
        """
        category = str(place.get("category", "")).lower()
        rating = float(place.get("rating", 4.0) or 4.0)
        place_price_tier = int(place.get("price_tier", 2) or 2)
        duration_min = int(place.get("visit_duration_min", 90) or 90)

        # 1. Interest Match Score (0.0 to 1.0)
        user_interests_lower = [i.lower() for i in user_interests] if user_interests else []
        if not user_interests_lower:
            interest_score = 0.7  # Neutral default
        elif category in user_interests_lower:
            interest_score = 1.0
        elif any(i in category for i in user_interests_lower):
            interest_score = 0.85
        else:
            interest_score = 0.3

        # 2. Rating Score (Normalized 1.0-5.0 -> 0.0-1.0)
        rating_score = max(0.0, min(1.0, (rating - 1.0) / 4.0))

        # 3. Budget Tier Alignment Score (0.0 to 1.0)
        # Closer match gives higher score
        diff = abs(place_price_tier - budget_tier)
        if diff == 0:
            budget_score = 1.0
        elif diff == 1:
            budget_score = 0.75
        elif diff == 2:
            budget_score = 0.45
        else:
            budget_score = 0.2

        # 4. Pace & Duration Score (0.0 to 1.0)
        if pace == "relaxed":
            # Prefers longer, relaxed visits (e.g. 90-180 min)
            pace_score = 1.0 if duration_min >= 90 else 0.7
        elif pace == "packed":
            # Prefers brisk visits (e.g. 45-90 min) to see more places
            pace_score = 1.0 if duration_min <= 90 else 0.75
        else: # balanced
            pace_score = 0.9

        # Calculate weighted composite score
        total_score = (
            cls.W_INTEREST * interest_score +
            cls.W_RATING * rating_score +
            cls.W_BUDGET * budget_score +
            cls.W_DIVERSITY * pace_score
        )

        return round(total_score, 4)
