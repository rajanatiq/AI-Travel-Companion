import uuid
from datetime import datetime, date, time
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator

# ==========================================
# AUTH & USER SCHEMAS
# ==========================================

class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    home_locale: Optional[str] = Field("en", max_length=10)
    full_name: Optional[str] = None
    phone_number: Optional[str] = None

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    age: Optional[int] = Field(None, ge=1, le=120)
    country: Optional[str] = None
    city: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    home_locale: Optional[str] = None

class PreferencesBase(BaseModel):
    interests: List[str] = Field(default_factory=list, description="e.g. ['food', 'history', 'art', 'nature']")
    pace_preference: str = Field("balanced", description="'relaxed', 'balanced', or 'packed'")
    default_budget_tier: int = Field(2, ge=1, le=4, description="1 (budget) to 4 (luxury)")

    @field_validator("pace_preference")
    @classmethod
    def validate_pace(cls, v: str) -> str:
        if v not in ("relaxed", "balanced", "packed"):
            raise ValueError("pace_preference must be 'relaxed', 'balanced', or 'packed'")
        return v

class PreferencesUpdate(PreferencesBase):
    pass

class PreferencesResponse(PreferencesBase):
    updated_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    home_locale: str
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    age: Optional[int] = None
    country: Optional[str] = None
    city: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    created_at: datetime
    preferences: Optional[PreferencesResponse] = None
    model_config = ConfigDict(from_attributes=True)

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse

class RefreshTokenRequest(BaseModel):
    refresh_token: str

# ==========================================
# ITINERARY ITEM SCHEMAS
# ==========================================

class ItineraryItemBase(BaseModel):
    day_index: int = Field(..., ge=0)
    order_index: int = Field(..., ge=0)
    place_id: Optional[str] = None
    name: str = Field(..., min_length=1, max_length=255)
    category: str = Field(..., description="history, food, nature, nightlife, art, adventure, family, shopping, culture, meal, transport")
    scheduled_time: str = Field(..., description="HH:MM (e.g. '09:30' or '09:30:00')")
    duration_min: int = Field(..., gt=0, description="Duration in minutes")
    est_cost: Optional[float] = Field(None, ge=0)
    crowd_level: Optional[str] = Field("medium", description="'low', 'medium', 'high'")
    lat: Optional[float] = None
    lon: Optional[float] = None
    opening_hours: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    user_edited: Optional[bool] = False

class ItineraryItemCreate(ItineraryItemBase):
    pass

class ItineraryItemUpdate(BaseModel):
    day_index: Optional[int] = Field(None, ge=0)
    order_index: Optional[int] = Field(None, ge=0)
    name: Optional[str] = None
    category: Optional[str] = None
    scheduled_time: Optional[str] = None
    duration_min: Optional[int] = Field(None, gt=0)
    est_cost: Optional[float] = Field(None, ge=0)
    crowd_level: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    notes: Optional[str] = None
    user_edited: Optional[bool] = True

class ItineraryItemResponse(BaseModel):
    id: uuid.UUID
    trip_id: uuid.UUID
    day_index: int
    order_index: int
    place_id: Optional[str] = None
    name: str
    category: str
    scheduled_time: str
    duration_min: int
    est_cost: Optional[float] = None
    crowd_level: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    opening_hours: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    user_edited: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

# ==========================================
# TRIP SCHEMAS
# ==========================================

class DayItinerary(BaseModel):
    day_index: int
    date: str
    day_budget_estimate: float
    items: List[ItineraryItemResponse]

class TripCreate(BaseModel):
    destination: str = Field(..., min_length=2, max_length=255, description="e.g. 'Lahore, Pakistan', 'Tokyo, Japan', 'Paris, France'")
    start_date: str = Field(..., description="YYYY-MM-DD")
    end_date: str = Field(..., description="YYYY-MM-DD")
    budget_total: float = Field(..., gt=0, description="Total budget amount in USD")
    interests: List[str] = Field(default_factory=list, description="e.g. ['food', 'art', 'history']")
    pace: Optional[str] = Field("balanced", description="'relaxed', 'balanced', 'packed'")

    @field_validator("pace")
    @classmethod
    def validate_pace(cls, v: str) -> str:
        if v not in ("relaxed", "balanced", "packed"):
            raise ValueError("pace must be 'relaxed', 'balanced', or 'packed'")
        return v

class TripUpdate(BaseModel):
    destination: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    budget_total: Optional[float] = Field(None, gt=0)
    interests: Optional[List[str]] = None
    pace: Optional[str] = None
    status: Optional[str] = Field(None, description="'draft', 'confirmed', 'completed', 'archived'")

class TripSummaryResponse(BaseModel):
    id: uuid.UUID
    destination: str
    start_date: str
    end_date: str
    budget_total: float
    interests: List[str]
    pace: str
    status: str
    cover_photo: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class TripDetailResponse(TripSummaryResponse):
    days: List[DayItinerary] = Field(default_factory=list)
    total_activities: int = 0
    estimated_total_cost: float = 0.0

# ==========================================
# EXPENSE SCHEMAS
# ==========================================

class ExpenseCreate(BaseModel):
    category: str = Field(..., description="meals, transport, activity, accommodation, shopping, other")
    amount: float = Field(..., gt=0)
    currency: str = Field("USD", min_length=3, max_length=3)
    note: Optional[str] = None
    logged_at: Optional[datetime] = None
    client_id: Optional[str] = None

class ExpenseResponse(BaseModel):
    id: uuid.UUID
    trip_id: uuid.UUID
    category: str
    amount: float
    currency: str
    note: Optional[str] = None
    logged_at: datetime
    synced_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)

class OfflineExpenseSyncItem(BaseModel):
    id: Optional[uuid.UUID] = None
    category: str
    amount: float
    currency: str = "USD"
    note: Optional[str] = None
    logged_at: datetime

class OfflineExpenseSyncRequest(BaseModel):
    expenses: List[OfflineExpenseSyncItem]

class OfflineExpenseSyncResponse(BaseModel):
    synced_count: int
    synced_ids: List[uuid.UUID]
    status: str = "success"

class TripBudgetSummaryResponse(BaseModel):
    trip_id: uuid.UUID
    destination: str
    budget_total: float
    spent: float
    remaining: float
    percent_spent: float
    daily_budget: float
    daily_spent: float
    daily_remaining: float
    category_breakdown: Dict[str, float]

# ==========================================
# EXTERNAL, DISCOVERY & CURRENCY SCHEMAS
# ==========================================

class PlacePOI(BaseModel):
    place_id: str
    name: str
    category: str
    rating: Optional[float] = 4.5
    price_tier: Optional[int] = 2
    lat: Optional[float] = 0.0
    lon: Optional[float] = 0.0
    description: Optional[str] = None
    photo_url: Optional[str] = None
    opening_hours: Optional[Dict[str, Any]] = None
    visit_duration_min: Optional[int] = 90
    est_cost: Optional[float] = 20.0

class CitySuggestion(BaseModel):
    city: str
    country: str
    destination: str
    flag: str
    currency_code: str
    currency_symbol: str
    exchange_rate_to_usd: float  # e.g. 155.20 for JPY, 278.50 for PKR
    avg_daily_cost_usd: float    # e.g. 85.0
    lat: float
    lon: float
    popular_places: List[str]
    time_zone: Optional[str] = None

class CurrencyConvertRequest(BaseModel):
    amount: float
    from_currency: str = "USD"
    to_currency: str = "JPY"

class CurrencyConvertResponse(BaseModel):
    amount: float
    from_currency: str
    to_currency: str
    rate: float
    converted_amount: float
    formatted: str

class WeatherForecastItem(BaseModel):
    date: str
    temp_high: Optional[float]
    temp_low: Optional[float]
    condition: Optional[str]
    humidity: Optional[int]
    wind_speed: Optional[float]

class EventItem(BaseModel):
    name: str
    date: str
    category: Optional[str] = None
    url: Optional[str] = None

class TranslationRequest(BaseModel):
    text: str
    target_language: str = "es"

class TranslationResponse(BaseModel):
    original_text: str
    translated_text: str
    target_language: str


class RatingCreate(BaseModel):
    score: int = Field(..., ge=1, le=5)
    review: Optional[str] = None

class RatingResponse(BaseModel):
    id: uuid.UUID
    trip_id: uuid.UUID
    score: int
    review: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True
