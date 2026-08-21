import uuid
from datetime import datetime, date, time, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Trip, ItineraryItem, Expense, User
from app.schemas import (
    TripCreate, TripUpdate, TripSummaryResponse, TripDetailResponse,
    DayItinerary, ItineraryItemResponse
)
from app.security import get_current_user
from app.services.places_service import PlacesService
from app.services.image_service import ImageService
from app.engine.scheduling import SchedulingEngine

router = APIRouter(prefix="/trips", tags=["Trip Planning & Itinerary"])

def format_trip_detail(trip: Trip) -> TripDetailResponse:
    """Helper to group ItineraryItems into structured DayItinerary objects."""
    items_by_day = {}
    total_cost = 0.0
    
    for item in trip.items:
        d_idx = item.day_index
        if d_idx not in items_by_day:
            items_by_day[d_idx] = []
        
        # Calculate total cost
        if item.est_cost:
            total_cost += float(item.est_cost)

        items_by_day[d_idx].append(ItineraryItemResponse(
            id=item.id,
            trip_id=item.trip_id,
            day_index=item.day_index,
            order_index=item.order_index,
            place_id=item.place_id,
            name=item.name,
            category=item.category,
            scheduled_time=str(item.scheduled_time),
            duration_min=item.duration_min,
            est_cost=float(item.est_cost) if item.est_cost is not None else None,
            crowd_level=item.crowd_level,
            lat=item.lat,
            lon=item.lon,
            opening_hours=item.opening_hours,
            notes=item.notes,
            user_edited=item.user_edited,
            created_at=item.created_at,
            updated_at=item.updated_at
        ))

    start_d = trip.start_date
    end_d = trip.end_date
    num_days = max(1, (end_d - start_d).days + 1)
    
    days_list = []
    for d_idx in range(num_days):
        from datetime import timedelta
        exact_day_date = (start_d + timedelta(days=d_idx)).strftime("%Y-%m-%d")
        
        day_items = items_by_day.get(d_idx, [])
        day_items.sort(key=lambda x: x.order_index)
        day_cost = sum((i.est_cost or 0.0) for i in day_items)

        days_list.append(DayItinerary(
            day_index=d_idx,
            date=exact_day_date,
            day_budget_estimate=round(day_cost, 2),
            items=day_items
        ))

    return TripDetailResponse(
        id=trip.id,
        destination=trip.destination,
        start_date=str(trip.start_date),
        end_date=str(trip.end_date),
        budget_total=float(trip.budget_total),
        interests=trip.interests or [],
        pace=trip.pace,
        status=trip.status,
        cover_photo=trip.cover_photo,
        created_at=trip.created_at,
        updated_at=trip.updated_at,
        days=days_list,
        total_activities=len(trip.items),
        estimated_total_cost=round(total_cost, 2)
    )

@router.post("", response_model=TripDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_trip(
    req: TripCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new trip and run the AI Itinerary Engine:
    1. Fetches candidate attractions & POIs.
    2. Runs multi-factor scoring against user preferences.
    3. Runs greedy day scheduling with meal slots and travel buffers.
    4. Persists trip and generated itinerary items into SQL Server.
    """
    try:
        start_d = datetime.strptime(req.start_date, "%Y-%m-%d").date()
        end_d = datetime.strptime(req.end_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Dates must be in YYYY-MM-DD format")
    
    if end_d < start_d:
        raise HTTPException(status_code=400, detail="end_date cannot be earlier than start_date")

    cover_photo = await ImageService.get_city_image(req.destination, db)

    trip_id = uuid.uuid4()
    new_trip = Trip(
        id=trip_id,
        user_id=current_user.id,
        destination=req.destination,
        cover_photo=cover_photo,
        start_date=start_d,
        end_date=end_d,
        budget_total=req.budget_total,
        interests=req.interests,
        pace=req.pace or "balanced",
        status="confirmed",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(new_trip)
    db.flush()

    candidates = await PlacesService.generate_candidate_places(
        destination=req.destination,
        interests=req.interests,
        db=db,
        limit=50
    )

    generated_days = SchedulingEngine.generate_itinerary(
        destination=req.destination,
        start_date_str=req.start_date,
        end_date_str=req.end_date,
        budget_total=req.budget_total,
        interests=req.interests,
        pace=req.pace or "balanced",
        candidate_places=candidates
    )

    for day in generated_days:
        for item in day["items"]:
            t_parts = item["scheduled_time"].split(":")
            time_obj = time(int(t_parts[0]), int(t_parts[1]), int(t_parts[2]) if len(t_parts) > 2 else 0)

            db_item = ItineraryItem(
                id=uuid.uuid4(),
                trip_id=trip_id,
                day_index=item["day_index"],
                order_index=item["order_index"],
                place_id=item.get("place_id"),
                name=item["name"],
                category=item["category"],
                scheduled_time=time_obj,
                duration_min=item["duration_min"],
                est_cost=item.get("est_cost"),
                crowd_level=item.get("crowd_level", "medium"),
                lat=item.get("lat"),
                lon=item.get("lon"),
                opening_hours=item.get("opening_hours"),
                notes=item.get("notes"),
                user_edited=False,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db.add(db_item)

    db.commit()
    db.refresh(new_trip)

    return format_trip_detail(new_trip)

@router.get("", response_model=List[TripSummaryResponse])
def list_trips(
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all trips created by the logged-in user."""
    query = db.query(Trip).filter(Trip.user_id == current_user.id)
    if status_filter:
        query = query.filter(Trip.status == status_filter)
    trips = query.order_by(Trip.created_at.desc()).all()
    
    return [
        TripSummaryResponse(
            id=t.id,
            destination=t.destination,
            start_date=str(t.start_date),
            end_date=str(t.end_date),
            budget_total=float(t.budget_total),
            interests=t.interests or [],
            pace=t.pace,
            status=t.status,
            cover_photo=t.cover_photo,
            created_at=t.created_at,
            updated_at=t.updated_at
        ) for t in trips
    ]

@router.get("/{trip_id}", response_model=TripDetailResponse)
def get_trip(
    trip_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve complete trip details with all day itineraries and scheduled items."""
    trip = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == current_user.id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    return format_trip_detail(trip)

@router.patch("/{trip_id}", response_model=TripSummaryResponse)
def update_trip(
    trip_id: uuid.UUID,
    req: TripUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update trip parameters or status."""
    trip = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == current_user.id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    if req.destination is not None:
        trip.destination = req.destination
    if req.start_date is not None:
        trip.start_date = datetime.strptime(req.start_date, "%Y-%m-%d").date()
    if req.end_date is not None:
        trip.end_date = datetime.strptime(req.end_date, "%Y-%m-%d").date()
    if req.budget_total is not None:
        trip.budget_total = req.budget_total
    if req.interests is not None:
        trip.interests = req.interests
    if req.pace is not None:
        trip.pace = req.pace
    if req.status is not None:
        trip.status = req.status
    
    trip.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(trip)

    return TripSummaryResponse(
        id=trip.id,
        destination=trip.destination,
        start_date=str(trip.start_date),
        end_date=str(trip.end_date),
        budget_total=float(trip.budget_total),
        interests=trip.interests or [],
        pace=trip.pace,
        status=trip.status,
        cover_photo=trip.cover_photo,
        created_at=trip.created_at,
        updated_at=trip.updated_at
    )

@router.delete("/{trip_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_trip(
    trip_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a trip and all its associated itinerary items and logged expenses
    permanently from SQL Server database.
    """
    trip = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == current_user.id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    try:
        db.query(ItineraryItem).filter(ItineraryItem.trip_id == trip_id).delete(synchronize_session=False)
        db.query(Expense).filter(Expense.trip_id == trip_id).delete(synchronize_session=False)
        db.delete(trip)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error deleting trip: {str(e)}")
    return None


from app.models import Rating
from app.schemas import RatingCreate, RatingResponse

@router.post("/{trip_id}/rating", response_model=RatingResponse)
def submit_rating(
    trip_id: uuid.UUID,
    req: RatingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit or update a rating for a specific trip."""
    trip = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == current_user.id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    rating = db.query(Rating).filter(Rating.trip_id == trip_id, Rating.user_id == current_user.id).first()
    if rating:
        rating.score = req.score
        rating.review = req.review
    else:
        rating = Rating(
            user_id=current_user.id,
            trip_id=trip_id,
            score=req.score,
            review=req.review
        )
        db.add(rating)
    db.commit()
    db.refresh(rating)
    return rating

@router.get("/{trip_id}/rating", response_model=RatingResponse)
def get_rating(
    trip_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the user's rating for a specific trip."""
    rating = db.query(Rating).filter(Rating.trip_id == trip_id, Rating.user_id == current_user.id).first()
    if not rating:
        raise HTTPException(status_code=404, detail="Rating not found")
    return rating
