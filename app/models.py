import uuid
import json
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Date, Time, 
    ForeignKey, Boolean, Text, Numeric, TypeDecorator, Uuid
)
from sqlalchemy.orm import relationship
from app.database import Base

# Custom TypeDecorator for storing Python lists/dicts as JSON in NVARCHAR(MAX) on SQL Server
class JSONText(TypeDecorator):
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        try:
            return json.loads(value)
        except Exception:
            return value

class User(Base):
    __tablename__ = "users"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    home_locale = Column(String(10), nullable=False, default="en")
    
    # Extended Profile Fields
    full_name = Column(String(255), nullable=True)
    phone_number = Column(String(50), nullable=True)
    age = Column(Integer, nullable=True)
    country = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    bio = Column(Text, nullable=True)
    avatar_url = Column(String(2048), nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    preferences = relationship("Preferences", back_populates="user", uselist=False, cascade="all, delete-orphan")
    trips = relationship("Trip", back_populates="user", cascade="all, delete-orphan")
    ratings = relationship("Rating", back_populates="user", cascade="all, delete-orphan")

class Preferences(Base):
    __tablename__ = "preferences"

    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    interests = Column(JSONText, nullable=False, default=list)  # JSON array: ["history", "food", "art"]
    pace_preference = Column(String(20), nullable=False, default="balanced")
    default_budget_tier = Column(Integer, nullable=False, default=2)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="preferences")

class Trip(Base):
    __tablename__ = "trips"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    destination = Column(String(255), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    budget_total = Column(Numeric(10, 2), nullable=False)
    interests = Column(JSONText, nullable=False, default=list)  # JSON array
    pace = Column(String(20), nullable=False, default="balanced")
    status = Column(String(20), nullable=False, default="draft", index=True)
    cover_photo = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="trips")
    items = relationship("ItineraryItem", back_populates="trip", cascade="all, delete-orphan", order_by="ItineraryItem.day_index, ItineraryItem.order_index")
    expenses = relationship("Expense", back_populates="trip", cascade="all, delete-orphan", order_by="Expense.logged_at.desc()")
    ratings = relationship("Rating", back_populates="trip", cascade="all, delete-orphan")

class ItineraryItem(Base):
    __tablename__ = "itinerary_items"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trip_id = Column(Uuid(as_uuid=True), ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)
    day_index = Column(Integer, nullable=False)
    order_index = Column(Integer, nullable=False)
    place_id = Column(String(255), nullable=True)
    name = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False)
    scheduled_time = Column(Time, nullable=False)
    duration_min = Column(Integer, nullable=False)
    est_cost = Column(Numeric(10, 2), nullable=True)
    crowd_level = Column(String(20), nullable=True)
    lat = Column(Numeric(10, 6), nullable=True)
    lon = Column(Numeric(10, 6), nullable=True)
    opening_hours = Column(JSONText, nullable=True)
    notes = Column(Text, nullable=True)
    user_edited = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    trip = relationship("Trip", back_populates="items")

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    trip_id = Column(Uuid(as_uuid=True), ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(50), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    note = Column(Text, nullable=True)
    logged_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    synced_at = Column(DateTime, nullable=True)

    trip = relationship("Trip", back_populates="expenses")

class PlacesCache(Base):
    __tablename__ = "places_cache"

    place_id = Column(String(255), primary_key=True)
    name = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False, index=True)
    lat = Column(Numeric(10, 6), nullable=True)
    lon = Column(Numeric(10, 6), nullable=True)
    price_tier = Column(Integer, nullable=True)
    rating = Column(Numeric(3, 2), nullable=True)
    opening_hours = Column(JSONText, nullable=True)
    visit_duration_min = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    photo_url = Column(String(2048), nullable=True)
    last_fetched = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)

class WeatherCache(Base):
    __tablename__ = "weather_cache"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    destination = Column(String(255), nullable=False, index=True)
    forecast_date = Column(Date, nullable=False)
    temp_high = Column(Numeric(5, 2), nullable=True)
    temp_low = Column(Numeric(5, 2), nullable=True)
    condition = Column(String(100), nullable=True)
    humidity = Column(Integer, nullable=True)
    wind_speed = Column(Numeric(5, 2), nullable=True)
    cached_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class EventsCache(Base):
    __tablename__ = "events_cache"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    destination = Column(String(255), nullable=False, index=True)
    event_date = Column(Date, nullable=False)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True)
    url = Column(String(2048), nullable=True)
    cached_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    trip_id = Column(Uuid(as_uuid=True), ForeignKey("trips.id", ondelete="NO ACTION"), nullable=False, index=True)
    score = Column(Integer, nullable=False)
    review = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="ratings")
    trip = relationship("Trip", back_populates="ratings")

class CityImageCache(Base):
    __tablename__ = "city_image_cache"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    city_name = Column(String(255), nullable=False, index=True)
    image_url = Column(String(2048), nullable=False)
    source = Column(String(50), nullable=False)
    fetched_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class VerifiedPlaceCache(Base):
    __tablename__ = "verified_place_cache"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    city_name = Column(String(255), nullable=False, index=True)
    country = Column(String(255), nullable=True)
    category = Column(String(50), nullable=False, index=True)
    place_id = Column(String(255), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    lat = Column(Numeric(10, 6), nullable=True)
    lng = Column(Numeric(10, 6), nullable=True)
    type_kind = Column(String(100), nullable=True)
    source = Column(String(50), nullable=False)
    fetched_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
