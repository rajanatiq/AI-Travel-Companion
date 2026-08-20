import json
import logging
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types
from app.config import settings

logger = logging.getLogger(__name__)

class AIPlacesService:
    PROMPT_TEMPLATE = """You are a trip-planning assistant. The user has selected a city and a category of interest. Your job is to return ONLY real, verified places that exist in that specific city and match the selected category exactly.

Inputs:
- city: {city}
- category: {category}

Rules:
1. Only return places that are physically located inside {city} — do not include places from nearby cities (e.g. if city = "Rawalpindi", do not include Islamabad-only places unless they are genuinely within Rawalpindi's boundaries).
2. Only return places that strictly match the selected category:
   - History → museums, forts, heritage sites, old bazaars, historical monuments
   - Food → restaurants, street food spots, famous local eateries
   - Nature → parks, lakes, hiking trails, gardens, viewpoints
3. Do NOT mix categories. If category = "History", do not include restaurants or parks even if they are popular.
4. For each place, return:
   - name (exact, real name)
   - short description (1–2 lines, why it fits the category)
   - exact location (full address or nearest landmark + latitude/longitude if available)
   - category tag (confirm it matches the input category)
5. If you are not fully certain a place exists in {city}, DO NOT include it. Never invent or guess place names.
6. Return results as a structured JSON list, sorted by relevance/popularity, minimum 3 and maximum 8 places.
7. If no verified places are found for that category in that city, return an empty array.

Output format MUST be valid JSON matching this schema:
{{
  "city": "{city}",
  "category": "{category}",
  "places": [
    {{
      "name": "Exact Name",
      "description": "Short Description",
      "location": "Location Info",
      "category_match": true
    }}
  ]
}}
"""

    @classmethod
    async def fetch_spots(cls, city: str, category: str) -> Dict[str, Any]:
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            logger.error("GEMINI_API_KEY is not set.")
            return {"error": "API Key is missing", "city": city, "category": category, "places": []}
            
        try:
            client = genai.Client(api_key=api_key)
            prompt = cls.PROMPT_TEMPLATE.format(city=city, category=category)
            
            response = client.models.generate_content(
                model='gemini-3.6-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )
            
            data = json.loads(response.text)
            return data
            
        except Exception as e:
            logger.error(f"Error fetching AI spots: {e}")
            return {"error": str(e), "city": city, "category": category, "places": []}


    PROMPT_BATCH_TEMPLATE = """You are a trip-planning assistant. The user has selected a city and multiple categories of interest. Your job is to return ONLY real, verified places that exist in that specific city for EACH of the provided categories.

Inputs:
- city: {city}
- categories: {categories}

Rules:
1. Only return places physically located inside {city}.
2. Only return places that strictly match the categories.
3. For each place, return name, short description, exact location, and category_match=true.
4. If you are not fully certain a place exists, DO NOT include it. Never invent names.
5. Return 3 to 6 places per category.

Output format MUST be valid JSON matching this schema:
{{
  "city": "{city}",
  "results": {{
    "category_name": [
      {{
        "name": "Exact Name",
        "description": "Short Description",
        "location": "Location Info",
        "category_match": true
      }}
    ]
  }}
}}
"""

    @classmethod
    async def fetch_spots_batch(cls, city: str, categories: List[str]) -> Dict[str, Any]:
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            return {"error": "API Key missing", "results": {}}
            
        try:
            client = genai.Client(api_key=api_key)
            prompt = cls.PROMPT_BATCH_TEMPLATE.format(city=city, categories=", ".join(categories))
            
            response = client.models.generate_content(
                model='gemini-3.6-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                ),
            )
            return json.loads(response.text)
        except Exception as e:
            logger.error(f"Error fetching AI spots batch: {e}")
            return {"error": str(e), "results": {}}
