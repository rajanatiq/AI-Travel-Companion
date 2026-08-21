import os
import logging
import httpx
import urllib.request
import urllib.parse
import json
import ssl
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models import CityImageCache
from app.config import settings

logger = logging.getLogger(__name__)

class ImageService:
    DEFAULT_PLACEHOLDER = "https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=1200&q=85"

    @classmethod
    async def get_city_image(cls, destination: str, db: Session) -> str:
        dest_clean = destination.strip().lower()
        
        try:
            cached = db.query(CityImageCache).filter(CityImageCache.city_name == dest_clean).first()
            if cached:
                return cached.image_url
        except Exception as e:
            logger.warning(f"Error querying CityImageCache: {e}")

        image_url = None
        source = None

        google_api_key = os.getenv("GOOGLE_PLACES_API_KEY")
        if not image_url and google_api_key:
            image_url = await cls._fetch_from_google_places(destination, google_api_key)
            if image_url:
                source = "google_places"

        if not image_url:
            image_url = await cls._fetch_from_wikipedia(destination)
            if image_url:
                source = "wikipedia"

        unsplash_key = os.getenv("UNSPLASH_ACCESS_KEY")
        if not image_url and unsplash_key:
            image_url = await cls._fetch_from_unsplash(destination, unsplash_key)
            if image_url:
                source = "unsplash"

        if not image_url:
            image_url = cls.DEFAULT_PLACEHOLDER
            source = "default"

        try:
            new_cache = CityImageCache(
                city_name=dest_clean,
                image_url=image_url,
                source=source,
                fetched_at=datetime.now(timezone.utc)
            )
            db.add(new_cache)
            db.commit()
        except Exception as e:
            logger.warning(f"Error saving to CityImageCache: {e}")
            db.rollback()

        return image_url

    @classmethod
    async def _fetch_from_google_places(cls, query: str, api_key: str) -> str:
        try:
            async with httpx.AsyncClient(headers={'User-Agent': 'WanderlustAIFallback-mq202/1.0 (dev_mq202_fix@local.test)'}, verify=False) as client:
                find_url = f"https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input={query}&inputtype=textquery&fields=photos&key={api_key}"
                r = await client.get(find_url, timeout=10.0)
                if r.status_code == 200:
                    data = r.json()
                    candidates = data.get("candidates", [])
                    if candidates and candidates[0].get("photos"):
                        photo_ref = candidates[0]["photos"][0]["photo_reference"]
                        return f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=1200&photoreference={photo_ref}&key={api_key}"
        except Exception as e:
            logger.warning(f"Google Places Image API error: {e}")
        return None

    @classmethod
    async def _fetch_from_wikipedia(cls, destination: str) -> str:
        city = destination.split(',')[0].strip()
        try:
            url = f"https://en.wikipedia.org/w/api.php?action=query&prop=pageimages&titles={urllib.parse.quote(city)}&pithumbsize=1200&format=json"
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            req = urllib.request.Request(url, headers={'User-Agent': 'WanderlustAIFallback-mq202/1.0 (dev_mq202_fix@local.test)'})
            with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
                data = json.loads(response.read().decode())
                pages = data.get("query", {}).get("pages", {})
                for page_id, page_data in pages.items():
                    if page_id != "-1" and "thumbnail" in page_data:
                        return page_data["thumbnail"]["source"]
        except Exception as e:
            logger.warning(f"Wikipedia Image API error: {e}")
        return None

    @classmethod
    async def _fetch_from_unsplash(cls, query: str, api_key: str) -> str:
        try:
            async with httpx.AsyncClient(headers={'User-Agent': 'WanderlustAIFallback-mq202/1.0 (dev_mq202_fix@local.test)'}, verify=False) as client:
                url = f"https://api.unsplash.com/search/photos?query={query} landmark&per_page=1&client_id={api_key}"
                r = await client.get(url, timeout=10.0)
                if r.status_code == 200:
                    data = r.json()
                    results = data.get("results", [])
                    if results:
                        return results[0]["urls"]["regular"]
        except Exception as e:
            logger.warning(f"Unsplash Image API error: {e}")
        return None
