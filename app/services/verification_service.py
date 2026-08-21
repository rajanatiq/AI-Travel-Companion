import os
import httpx
import urllib.request
import urllib.parse
import json
import ssl
import logging
import urllib.parse
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Set
from app.models import VerifiedPlaceCache

logger = logging.getLogger(__name__)

class VerificationService:
    # Strict taxonomy mapping for categories
    CATEGORY_MAP = {
        "history": {
            "opentripmap": ["historic", "monuments_and_memorials", "museums", "archaeology", "fortifications"],
            "google": ["museum", "tourist_attraction", "historic_site", "landmark"],
            "wiki": ["museum", "fort", "mosque", "tomb", "monument", "heritage", "history", "archaeological"]
        },
        "nature": {
            "opentripmap": ["natural", "nature_reserves", "water", "beaches", "geological_formations"],
            "google": ["park", "natural_feature", "national_park", "campground"],
            "wiki": ["park", "lake", "river", "mountain", "hill", "garden", "reserve", "dam"]
        },
        "food": {
            "opentripmap": ["foods", "restaurants", "cafes", "fast_food", "food_courts"],
            "google": ["restaurant", "cafe", "bakery", "meal_takeaway", "food"],
            "wiki": ["restaurant", "cafe", "bazaar", "market"] # Food is hard on wiki
        },
        "shopping": {
            "opentripmap": ["shops", "malls", "marketplaces"],
            "google": ["shopping_mall", "store", "market", "clothing_store", "supermarket"],
            "wiki": ["mall", "market", "bazaar", "avenue", "street"]
        },
        "adventure": {
            "opentripmap": ["sport", "amusements", "climbing", "diving"],
            "google": ["amusement_park", "stadium", "campground"],
            "wiki": ["stadium", "park", "arena", "complex", "sports"]
        },
        "religion": {
            "opentripmap": ["religion", "churches", "mosques", "temples"],
            "google": ["place_of_worship", "church", "mosque", "hindu_temple", "synagogue"],
            "wiki": ["mosque", "church", "temple", "shrine", "cathedral", "gurdwara"]
        },
        "nightlife": {
            "opentripmap": ["adult", "amusements", "pubs", "bars", "nightclubs"],
            "google": ["night_club", "bar", "casino"],
            "wiki": ["club", "bar", "theatre", "cinema"]
        },
        "culture": {
            "opentripmap": ["cultural", "theatres_and_entertainments"],
            "google": ["art_gallery", "museum", "tourist_attraction", "library"],
            "wiki": ["gallery", "museum", "theatre", "library", "institute", "art"]
        },
        "family": {
            "opentripmap": ["amusements", "zoos"],
            "google": ["zoo", "amusement_park", "park", "aquarium"],
            "wiki": ["zoo", "park", "aquarium", "museum"]
        }
    }

    # Types that indicate an entity is NOT a visitable place
    FORBIDDEN_TYPES = {
        "google": ["political", "locality", "country", "administrative_area_level_1", "route", 
                   "organization", "sports_club", "local_government_office", "premise"],
        "opentripmap": ["unclassified"]
    }
    
    @classmethod
    async def verify_and_fetch_places(
        cls, 
        city_name: str, 
        base_lat: float, 
        base_lon: float,
        categories: List[str], 
        gemini_suggestions: List[Dict[str, Any]], 
        db: Session
    ) -> List[Dict[str, Any]]:
        
        verified_candidates = []
        city_key = city_name.strip().lower()
        
        # 1. Pull from Cache first
        for cat in categories:
            try:
                cached_spots = db.query(VerifiedPlaceCache).filter(
                    VerifiedPlaceCache.city_name == city_key,
                    VerifiedPlaceCache.category == cat
                ).all()
                for c in cached_spots:
                    verified_candidates.append({
                        "place_id": c.place_id,
                        "name": c.name,
                        "category": c.category,
                        "rating": 4.5,
                        "price_tier": 2,
                        "lat": float(c.lat) if c.lat else base_lat,
                        "lon": float(c.lng) if c.lng else base_lon,
                        "address": f"{c.name}, {city_name}",
                        "opening_hours": {"open": "09:00", "close": "21:00"},
                        "visit_duration_min": 90,
                        "description": f"Verified {cat} spot in {city_name}.",
                        "photo_url": "https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=700&q=80",
                        "est_cost": 15.0
                    })
            except Exception as e:
                logger.warning(f"Error reading VerifiedPlaceCache: {e}")

        # If we have enough cached spots for each category, we can just return
        cat_counts = {c: 0 for c in categories}
        for v in verified_candidates:
            cat_counts[v["category"]] += 1
            
        if all(count >= 4 for count in cat_counts.values()):
            return verified_candidates

        google_key = os.getenv("GOOGLE_PLACES_API_KEY")
        
        # We will use Wikipedia GeoSearch as baseline for all cities
        wiki_geo_spots = await cls._fetch_wikipedia_geosearch(base_lat, base_lon, radius_meters=10000)
        
        # We will map AI suggestions and verify them
        for cat in categories:
            if cat_counts[cat] >= 4:
                continue
                
            ai_spots_for_cat = [s for s in gemini_suggestions if s.get("category", "").lower() == cat or s.get("category_match")]
            
            for ai_spot in ai_spots_for_cat:
                if cat_counts[cat] >= 4:
                    break
                    
                ai_name = ai_spot.get("name", "")
                
                # Check Google Places if available
                if google_key:
                    is_verified, v_data = await cls._verify_google(ai_name, city_name, cat, google_key, base_lat, base_lon)
                    if is_verified:
                        cls._save_to_cache(db, city_key, cat, v_data)
                        verified_candidates.append(v_data)
                        cat_counts[cat] += 1
                        continue
                
                # Check Wikipedia Geosearch (Strict coordinate check)
                is_verified, v_data = cls._verify_wiki(ai_name, cat, wiki_geo_spots, city_name)
                if is_verified:
                    cls._save_to_cache(db, city_key, cat, v_data)
                    verified_candidates.append(v_data)
                    cat_counts[cat] += 1
                    continue
                    
            # If we still lack places for this category, try to mine from Wikipedia GeoSearch
            if cat_counts[cat] < 4 and not google_key:
                mined = cls._mine_wiki(wiki_geo_spots, cat, city_name)
                for v_data in mined:
                    if cat_counts[cat] >= 4:
                        break
                    # Avoid duplicates
                    if not any(c["place_id"] == v_data["place_id"] for c in verified_candidates):
                        cls._save_to_cache(db, city_key, cat, v_data)
                        verified_candidates.append(v_data)
                        cat_counts[cat] += 1

        return verified_candidates

    @classmethod
    async def _verify_google(cls, name: str, city: str, category: str, api_key: str, lat: float, lon: float):
        try:
            query = f"{name} in {city}"
            url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={urllib.parse.quote(query)}&key={api_key}"
            async with httpx.AsyncClient(headers={'User-Agent': 'WanderlustAIFallback-mq202/1.0 (dev_mq202_fix@local.test)'}, verify=False) as client:
                r = await client.get(url, timeout=10.0)
                if r.status_code == 200:
                    data = r.json()
                    results = data.get("results", [])
                    if results:
                        first = results[0]
                        types = first.get("types", [])
                        
                        # 1. Reject forbidden entity types (e.g., organizations, leagues, countries)
                        if any(t in cls.FORBIDDEN_TYPES["google"] for t in types):
                            return False, None
                            
                        # 2. Check taxonomy
                        allowed_types = cls.CATEGORY_MAP.get(category, {}).get("google", [])
                        if not allowed_types: # fallback
                            allowed_types = ["tourist_attraction", "point_of_interest", "establishment"]
                            
                        if not any(t in allowed_types for t in types) and "point_of_interest" not in types:
                            return False, None
                            
                        geo = first.get("geometry", {}).get("location", {})
                        if not geo:
                            return False, None

                        v_data = {
                            "place_id": f"g_{first['place_id']}",
                            "name": first["name"],
                            "category": category,
                            "rating": first.get("rating", 4.5),
                            "price_tier": first.get("price_level", 2),
                            "lat": geo.get("lat", lat),
                            "lon": geo.get("lng", lon),
                            "address": first.get("formatted_address", f"{city}"),
                            "opening_hours": {"open": "09:00", "close": "21:00"},
                            "visit_duration_min": 90,
                            "description": f"Verified {category} spot in {city}.",
                            "photo_url": "https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=700&q=80",
                            "est_cost": 15.0
                        }
                        return True, v_data
        except Exception:
            pass
        return False, None

    @classmethod
    async def _fetch_wikipedia_geosearch(cls, lat: float, lon: float, radius_meters: int = 10000) -> List[Dict[str, Any]]:
        try:
            url = f"https://en.wikipedia.org/w/api.php?action=query&list=geosearch&gscoord={lat}|{lon}&gsradius={radius_meters}&gslimit=500&format=json"
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            req = urllib.request.Request(url, headers={'User-Agent': 'WanderlustAIFallback-mq202/1.0 (dev_mq202_fix@local.test)'})
            with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
                data = json.loads(response.read().decode())
                return data.get("query", {}).get("geosearch", [])
        except Exception as e:
            logger.warning(f"Wiki GeoSearch error: {e}")
        return []

    @classmethod
    def _verify_wiki(cls, name: str, category: str, wiki_spots: List[Dict[str, Any]], city_name: str):
        if not name or not wiki_spots:
            return False, None
            
        name_lower = name.lower()
        
        for spot in wiki_spots:
            title = spot["title"].lower()
            # If name is a subset of title or title is a subset of name
            if name_lower in title or title in name_lower or cls._similarity(name_lower, title) > 0.7:
                # Wikipedia Geosearch guarantees coordinates, so it's a physical place!
                v_data = {
                    "place_id": f"w_{spot['pageid']}",
                    "name": spot["title"],
                    "category": category,
                    "rating": 4.5,
                    "price_tier": 2,
                    "lat": spot["lat"],
                    "lon": spot["lon"],
                    "address": f"{spot['title']}, {city_name}",
                    "opening_hours": {"open": "09:00", "close": "21:00"},
                    "visit_duration_min": 90,
                    "description": f"Verified physical location from Wikipedia.",
                    "photo_url": "https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=700&q=80",
                    "est_cost": 10.0
                }
                return True, v_data
        return False, None

    @classmethod
    def _mine_wiki(cls, wiki_spots: List[Dict[str, Any]], category: str, city_name: str) -> List[Dict[str, Any]]:
        mined = []
        allowed_keywords = cls.CATEGORY_MAP.get(category, {}).get("wiki", [])
        if not allowed_keywords:
            return mined
            
        for spot in wiki_spots:
            title = spot["title"].lower()
            if any(kw in title for kw in allowed_keywords):
                v_data = {
                    "place_id": f"w_{spot['pageid']}",
                    "name": spot["title"],
                    "category": category,
                    "rating": 4.5,
                    "price_tier": 1,
                    "lat": spot["lat"],
                    "lon": spot["lon"],
                    "address": f"{spot['title']}, {city_name}",
                    "opening_hours": {"open": "09:00", "close": "21:00"},
                    "visit_duration_min": 90,
                    "description": f"Verified physical location from Wikipedia.",
                    "photo_url": "https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=700&q=80",
                    "est_cost": 5.0
                }
                mined.append(v_data)
        return mined

    @classmethod
    def _save_to_cache(cls, db: Session, city_key: str, category: str, v_data: dict):
        try:
            existing = db.query(VerifiedPlaceCache).filter(VerifiedPlaceCache.place_id == v_data["place_id"]).first()
            if not existing:
                c = VerifiedPlaceCache(
                    city_name=city_key,
                    category=category,
                    place_id=v_data["place_id"],
                    name=v_data["name"],
                    lat=v_data["lat"],
                    lng=v_data["lon"],
                    type_kind="verified",
                    source="verification_service",
                    fetched_at=datetime.now(timezone.utc)
                )
                db.add(c)
                db.commit()
        except Exception:
            db.rollback()

    @staticmethod
    def _similarity(s1: str, s2: str) -> float:
        # Super simple Jaccard similarity for token overlap
        set1 = set(s1.split())
        set2 = set(s2.split())
        if not set1 or not set2:
            return 0.0
        return len(set1.intersection(set2)) / len(set1.union(set2))
