import uuid
from datetime import datetime, time, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Trip, ItineraryItem, User
from app.schemas import ItineraryItemCreate, ItineraryItemUpdate, ItineraryItemResponse
from app.security import get_current_user

router = APIRouter(prefix="/trips/{trip_id}/items", tags=["Itinerary Manipulation"])

def parse_time_str(time_str: str) -> time:
    parts = time_str.split(":")
    return time(int(parts[0]), int(parts[1]), int(parts[2]) if len(parts) > 2 else 0)

@router.post("", response_model=ItineraryItemResponse, status_code=status.HTTP_201_CREATED)
def add_itinerary_item(
    trip_id: uuid.UUID,
    item_in: ItineraryItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually add an attraction or custom activity to an itinerary."""
    trip = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == current_user.id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    new_item = ItineraryItem(
        id=uuid.uuid4(),
        trip_id=trip_id,
        day_index=item_in.day_index,
        order_index=item_in.order_index,
        place_id=item_in.place_id,
        name=item_in.name,
        category=item_in.category,
        scheduled_time=parse_time_str(item_in.scheduled_time),
        duration_min=item_in.duration_min,
        est_cost=item_in.est_cost,
        crowd_level=item_in.crowd_level or "medium",
        lat=item_in.lat,
        lon=item_in.lon,
        opening_hours=item_in.opening_hours,
        notes=item_in.notes,
        user_edited=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(new_item)
    db.commit()
    db.refresh(new_item)

    return ItineraryItemResponse(
        id=new_item.id,
        trip_id=new_item.trip_id,
        day_index=new_item.day_index,
        order_index=new_item.order_index,
        place_id=new_item.place_id,
        name=new_item.name,
        category=new_item.category,
        scheduled_time=new_item.scheduled_time.strftime("%H:%M"),
        duration_min=new_item.duration_min,
        est_cost=float(new_item.est_cost) if new_item.est_cost is not None else None,
        crowd_level=new_item.crowd_level,
        lat=float(new_item.lat) if new_item.lat is not None else None,
        lon=float(new_item.lon) if new_item.lon is not None else None,
        opening_hours=new_item.opening_hours,
        notes=new_item.notes,
        user_edited=new_item.user_edited,
        created_at=new_item.created_at,
        updated_at=new_item.updated_at
    )

@router.patch("/{item_id}", response_model=ItineraryItemResponse)
def update_itinerary_item(
    trip_id: uuid.UUID,
    item_id: uuid.UUID,
    item_in: ItineraryItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Edit, swap, or reschedule an itinerary item (marks as user_edited)."""
    trip = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == current_user.id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    item = db.query(ItineraryItem).filter(ItineraryItem.id == item_id, ItineraryItem.trip_id == trip_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Itinerary item not found")

    if item_in.day_index is not None:
        item.day_index = item_in.day_index
    if item_in.order_index is not None:
        item.order_index = item_in.order_index
    if item_in.name is not None:
        item.name = item_in.name
    if item_in.category is not None:
        item.category = item_in.category
    if item_in.scheduled_time is not None:
        item.scheduled_time = parse_time_str(item_in.scheduled_time)
    if item_in.duration_min is not None:
        item.duration_min = item_in.duration_min
    if item_in.est_cost is not None:
        item.est_cost = item_in.est_cost
    if item_in.crowd_level is not None:
        item.crowd_level = item_in.crowd_level
    if item_in.lat is not None:
        item.lat = item_in.lat
    if item_in.lon is not None:
        item.lon = item_in.lon
    if item_in.notes is not None:
        item.notes = item_in.notes
    
    item.user_edited = True
    item.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(item)

    return ItineraryItemResponse(
        id=item.id,
        trip_id=item.trip_id,
        day_index=item.day_index,
        order_index=item.order_index,
        place_id=item.place_id,
        name=item.name,
        category=item.category,
        scheduled_time=item.scheduled_time.strftime("%H:%M") if isinstance(item.scheduled_time, time) else str(item.scheduled_time),
        duration_min=item.duration_min,
        est_cost=float(item.est_cost) if item.est_cost is not None else None,
        crowd_level=item.crowd_level,
        lat=float(item.lat) if item.lat is not None else None,
        lon=float(item.lon) if item.lon is not None else None,
        opening_hours=item.opening_hours,
        notes=item.notes,
        user_edited=item.user_edited,
        created_at=item.created_at,
        updated_at=item.updated_at
    )

@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_itinerary_item(
    trip_id: uuid.UUID,
    item_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an item from the itinerary."""
    trip = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == current_user.id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    item = db.query(ItineraryItem).filter(ItineraryItem.id == item_id, ItineraryItem.trip_id == trip_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Itinerary item not found")

    db.delete(item)
    db.commit()
    return None
