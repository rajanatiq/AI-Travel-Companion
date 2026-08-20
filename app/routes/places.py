from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import PlacePOI, CitySuggestion
from app.services.places_service import PlacesService

router = APIRouter(prefix="/places", tags=["Places & Discovery"])

@router.get("/cities/autocomplete", response_model=List[CitySuggestion])
def autocomplete_cities(
    q: str = Query("", description="Prefix or keyword to search cities e.g. 't', 'to', 'lah'"),
    limit: int = Query(10, ge=1, le=25)
):
    """
    Real-time city search & autocomplete. Returns matching worldwide cities 
    with local currencies, exchange rates to USD, and signature attractions.
    """
    return PlacesService.autocomplete_cities(query=q, limit=limit)

@router.get("/cities/details", response_model=CitySuggestion)
def get_city_details(
    destination: str = Query(..., description="Destination name e.g. 'Tokyo, Japan'")
):
    """Get currency, live exchange rate, and top places for a destination."""
    return PlacesService.get_city_details(destination=destination)

@router.get("/search", response_model=List[PlacePOI])
async def search_places(
    q: str = Query(..., min_length=1, description="Search query or keyword"),
    destination: Optional[str] = Query(None, description="Optional city / destination context"),
    db: Session = Depends(get_db)
):
    """Search for places, POIs, and attractions with auto-complete capability."""
    results = await PlacesService.search_places(query=q, destination=destination, db=db)
    return results

@router.get("/nearby", response_model=List[PlacePOI])
async def get_nearby_places(
    destination: str = Query(..., description="Destination e.g. 'Paris, France'"),
    category: Optional[str] = Query(None, description="history, food, art, nature, etc."),
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Explore top attractions and POIs for a destination."""
    interests = [category] if category else None
    results = await PlacesService.generate_candidate_places(destination=destination, interests=interests, db=db, limit=limit)
    return results
