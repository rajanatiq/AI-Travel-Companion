from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import (
    WeatherForecastItem, EventItem, TranslationRequest, TranslationResponse,
    CurrencyConvertResponse
)
from app.services.weather_service import WeatherService
from app.services.ai_places_service import AIPlacesService
from app.services.events_service import EventsService
from app.services.places_service import WORLDWIDE_CITIES_DATABASE

router = APIRouter(prefix="/discovery", tags=["Weather, Events & Utilities"])

@router.get("/weather", response_model=List[WeatherForecastItem])
async def get_weather(
    destination: str = Query(..., description="Destination city name"),
    start_date: str = Query(..., description="YYYY-MM-DD"),
    end_date: str = Query(..., description="YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    """Fetch weather forecast for travel duration."""
    return await WeatherService.get_forecast(destination, start_date, end_date, db=db)

@router.get("/events", response_model=List[EventItem])
async def get_events(
    destination: str = Query(..., description="Destination city name"),
    start_date: str = Query(..., description="YYYY-MM-DD"),
    end_date: str = Query(..., description="YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    """Discover local events, festivals, and concerts."""
    return await EventsService.get_events(destination, start_date, end_date, db=db)

@router.get("/currency/convert", response_model=CurrencyConvertResponse)
def convert_currency(
    amount: float = Query(..., gt=0, description="Amount to convert"),
    from_currency: str = Query("USD", description="Base currency e.g. USD"),
    to_currency: str = Query("JPY", description="Target currency e.g. JPY, PKR, EUR, AED, GBP")
):
    """Live exchange rate conversion calculator."""
    from_c = from_currency.upper().strip()
    to_c = to_currency.upper().strip()

    rates_to_usd: Dict[str, float] = {
        "USD": 1.0,
        "EUR": 0.92,
        "GBP": 0.78,
        "JPY": 155.20,
        "PKR": 278.50,
        "AED": 3.67,
        "TRY": 34.10,
        "CAD": 1.36,
        "AUD": 1.52,
        "SAR": 3.75,
        "QAR": 3.64,
        "EGP": 48.60,
        "ZAR": 18.20,
        "THB": 36.50,
        "SGD": 1.35,
        "IDR": 15800.0,
        "KRW": 1380.0,
        "TWD": 32.40,
        "CZK": 23.20,
        "GEL": 2.72,
        "UZS": 12700.0,
        "TND": 3.10,
        "BRL": 5.50
    }

    # Extract rates from worldwide cities if exists
    for item in WORLDWIDE_CITIES_DATABASE:
        rates_to_usd[item["currency_code"]] = item["exchange_rate_to_usd"]

    rate_from = rates_to_usd.get(from_c, 1.0)
    rate_to = rates_to_usd.get(to_c, 1.0)

    # Convert: from_amount -> USD -> to_amount
    usd_val = amount / rate_from if rate_from > 0 else amount
    converted = round(usd_val * rate_to, 2)
    effective_rate = round(rate_to / rate_from, 4) if rate_from > 0 else rate_to

    symbols = {
        "USD": "$", "EUR": "€", "GBP": "£", "JPY": "¥", "PKR": "Rs", 
        "AED": "د.إ", "TRY": "₺", "CAD": "CA$", "AUD": "A$", "SAR": "﷼",
        "EGP": "E£", "ZAR": "R", "THB": "฿", "SGD": "S$", "IDR": "Rp", "KRW": "₩"
    }
    sym = symbols.get(to_c, to_c)

    return CurrencyConvertResponse(
        amount=amount,
        from_currency=from_c,
        to_currency=to_c,
        rate=effective_rate,
        converted_amount=converted,
        formatted=f"{sym} {converted:,.2f} {to_c}"
    )



@router.get("/ai-spots")
async def get_ai_spots(
    city: str = Query(..., description="Destination city name"),
    category: str = Query(..., description="Category (History, Food, Nature, Shopping, etc.)")
):
    """Dynamically generate verified travel spots using AI."""
    return await AIPlacesService.fetch_spots(city, category)
