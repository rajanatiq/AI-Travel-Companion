"""
Rule-based crowd estimation heuristic.
Calculates crowd level ('low', 'medium', 'high') based on category, hour, and day of week.
"""

def estimate_crowd_level(category: str, hour: int, is_weekend: bool = False) -> str:
    category = (category or "").lower()
    
    # Dining peak hours
    if category in ("food", "meal"):
        if (12 <= hour <= 14) or (19 <= hour <= 21):
            return "high"
        elif (11 <= hour < 12) or (17 <= hour < 19):
            return "medium"
        else:
            return "low"
    
    # Nightlife peak
    if category == "nightlife":
        if hour >= 21 or hour < 2:
            return "high"
        elif 18 <= hour < 21:
            return "medium"
        else:
            return "low"
    
    # Major tourist spots, museums, historical sites
    if category in ("history", "art", "culture", "adventure", "family", "shopping"):
        if is_weekend:
            if 11 <= hour <= 17:
                return "high"
            elif 9 <= hour < 11 or 17 < hour <= 19:
                return "medium"
            else:
                return "low"
        else:
            if 13 <= hour <= 16:
                return "high"
            elif 10 <= hour < 13 or 16 < hour <= 18:
                return "medium"
            else:
                return "low"
    
    # Nature / Parks / Outdoor
    if category == "nature":
        if 11 <= hour <= 15 and is_weekend:
            return "medium"
        return "low"
    
    return "medium"
