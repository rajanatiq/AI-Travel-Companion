import os
filepath = r'C:\Users\mq202\PycharmProjects\AI Travel Companion\app\services\places_service.py'
with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# I need to replace the entire generate_candidate_places function.
import re
pattern = re.compile(r'    @classmethod\s+async def generate_candidate_places.*?return candidates\[:limit\]', re.DOTALL)

new_func = '''    @classmethod
    async def generate_candidate_places(
        cls,
        destination: str,
        interests: List[str] = None,
        db: Optional[Session] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Generates 100% REAL, EXACT, GEOLOCATED places matching user's selected vibes/interests.
        Uses VerifiedPlaceCache, Wikipedia Geosearch, and AI verification.
        """
        from app.services.verification_service import VerificationService
        from app.services.ai_places_service import AIPlacesService

        city_info = cls.get_city_details(destination)
        city_name = city_info["city"]
        city_key = city_name.lower().strip()
        
        interests = interests or ["history", "food", "culture", "nature", "art"]
        categories = list(set([i.lower() for i in interests] + ["food", "history", "culture", "nature"]))

        base_lat = city_info["lat"]
        base_lon = city_info["lon"]

        # Fetch candidate spots from Gemini (AI)
        batch_res = await AIPlacesService.fetch_spots_batch(city_name, categories)
        results_dict = batch_res.get("results", {})
        
        gemini_suggestions = []
        for cat, places in results_dict.items():
            if isinstance(places, list):
                for p in places:
                    p["category"] = cat.lower()
                    gemini_suggestions.append(p)
                    
        # Verify suggestions and fetch alternatives if needed
        verified_candidates = await VerificationService.verify_and_fetch_places(
            city_name=city_name,
            base_lat=base_lat,
            base_lon=base_lon,
            categories=categories,
            gemini_suggestions=gemini_suggestions,
            db=db
        )
        
        # Save to PlacesCache for legacy support if needed
        if db:
            for poi_data in verified_candidates:
                try:
                    p_id = poi_data["place_id"]
                    from app.models import PlacesCache
                    existing = db.query(PlacesCache).filter(PlacesCache.place_id == p_id).first()
                    if not existing:
                        db_place = PlacesCache(
                            place_id=p_id,
                            name=poi_data["name"],
                            category=poi_data["category"],
                            lat=poi_data["lat"],
                            lon=poi_data["lon"],
                            price_tier=poi_data["price_tier"],
                            rating=poi_data["rating"],
                            opening_hours=poi_data["opening_hours"],
                            visit_duration_min=poi_data["visit_duration_min"],
                            description=poi_data["description"],
                            photo_url=poi_data["photo_url"],
                            last_fetched=datetime.now(timezone.utc)
                        )
                        db.add(db_place)
                except Exception:
                    pass
            try:
                db.commit()
            except Exception:
                db.rollback()

        return verified_candidates[:limit]'''

if pattern.search(content):
    content = pattern.sub(new_func, content)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print("Patched generate_candidate_places in places_service.py!")
else:
    print("Regex match failed.")
