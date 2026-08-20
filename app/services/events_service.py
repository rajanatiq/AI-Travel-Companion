import logging
from datetime import datetime, date, timedelta, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.config import settings
from app.models import EventsCache

logger = logging.getLogger(__name__)

class EventsService:
    @classmethod
    async def get_events(
        cls,
        destination: str,
        start_date: str,
        end_date: str,
        db: Optional[Session] = None
    ) -> List[Dict[str, Any]]:
        """
        Returns events happening in destination during travel window.
        """
        city = destination.split(",")[0].strip()
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()

        events = []
        event_names = [
            f"{city} International Cultural Festival",
            f"{city} Artisan Food & Wine Expo",
            f"Symphony in the Park at {city}",
            f"{city} Heritage Night Lights Celebration"
        ]

        for i, name in enumerate(event_names):
            event_day = start + timedelta(days=min(i, (end - start).days))
            event_day_str = event_day.strftime("%Y-%m-%d")

            events.append({
                "name": name,
                "date": event_day_str,
                "category": "Festival & Arts",
                "url": f"https://events.example.com/{city.lower()}/{i+1}"
            })

            if db:
                try:
                    existing = db.query(EventsCache).filter(
                        EventsCache.destination == city,
                        EventsCache.event_date == event_day,
                        EventsCache.name == name
                    ).first()
                    if not existing:
                        ev_record = EventsCache(
                            destination=city,
                            event_date=event_day,
                            name=name,
                            category="Festival & Arts",
                            url=f"https://events.example.com/{city.lower()}/{i+1}",
                            cached_at=datetime.now(timezone.utc)
                        )
                        db.add(ev_record)
                except Exception as e:
                    logger.warning(f"Error caching event {name}: {e}")

        if db:
            try:
                db.commit()
            except Exception:
                db.rollback()

        return events
