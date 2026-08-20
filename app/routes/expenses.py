import uuid
from datetime import datetime, date, timezone
from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import Trip, Expense, User
from app.schemas import (
    ExpenseCreate, ExpenseResponse, OfflineExpenseSyncRequest,
    OfflineExpenseSyncResponse, TripBudgetSummaryResponse
)
from app.security import get_current_user

router = APIRouter(prefix="/trips/{trip_id}/expenses", tags=["Expense Tracking & Offline Sync"])

@router.post("", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def log_expense(
    trip_id: uuid.UUID,
    exp_in: ExpenseCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Log a new travel expense for a trip."""
    trip = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == current_user.id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    new_expense = Expense(
        id=uuid.uuid4(),
        trip_id=trip_id,
        category=exp_in.category,
        amount=exp_in.amount,
        currency=exp_in.currency.upper(),
        note=exp_in.note,
        logged_at=exp_in.logged_at or datetime.now(timezone.utc),
        synced_at=datetime.now(timezone.utc)
    )
    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)

    return ExpenseResponse(
        id=new_expense.id,
        trip_id=new_expense.trip_id,
        category=new_expense.category,
        amount=float(new_expense.amount),
        currency=new_expense.currency,
        note=new_expense.note,
        logged_at=new_expense.logged_at,
        synced_at=new_expense.synced_at
    )

@router.get("", response_model=List[ExpenseResponse])
def list_expenses(
    trip_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all recorded expenses for a trip."""
    trip = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == current_user.id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    expenses = db.query(Expense).filter(Expense.trip_id == trip_id).order_by(Expense.logged_at.desc()).all()
    return [
        ExpenseResponse(
            id=e.id,
            trip_id=e.trip_id,
            category=e.category,
            amount=float(e.amount),
            currency=e.currency,
            note=e.note,
            logged_at=e.logged_at,
            synced_at=e.synced_at
        ) for e in expenses
    ]

@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expense(
    trip_id: uuid.UUID,
    expense_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a logged expense."""
    trip = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == current_user.id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    expense = db.query(Expense).filter(Expense.id == expense_id, Expense.trip_id == trip_id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    db.delete(expense)
    db.commit()
    return None

@router.post("/sync", response_model=OfflineExpenseSyncResponse)
def sync_offline_expenses(
    trip_id: uuid.UUID,
    req: OfflineExpenseSyncRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Batch synchronize offline expenses logged by the client app when disconnected.
    Supports idempotent inserts and reconciliation.
    """
    trip = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == current_user.id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    synced_ids = []
    for item in req.expenses:
        exp_id = item.id or uuid.uuid4()
        existing = db.query(Expense).filter(Expense.id == exp_id).first()
        if not existing:
            new_exp = Expense(
                id=exp_id,
                trip_id=trip_id,
                category=item.category,
                amount=item.amount,
                currency=item.currency.upper(),
                note=item.note,
                logged_at=item.logged_at,
                synced_at=datetime.now(timezone.utc)
            )
            db.add(new_exp)
        else:
            existing.synced_at = datetime.now(timezone.utc)
        
        synced_ids.append(exp_id)

    db.commit()
    return OfflineExpenseSyncResponse(
        synced_count=len(synced_ids),
        synced_ids=synced_ids,
        status="success"
    )

@router.get("/budget/summary", response_model=TripBudgetSummaryResponse)
def get_trip_budget_summary(
    trip_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Compute real-time budget analytics: total spent, remaining, daily budget vs daily spent, category breakdown.
    """
    trip = db.query(Trip).filter(Trip.id == trip_id, Trip.user_id == current_user.id).first()
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    expenses = db.query(Expense).filter(Expense.trip_id == trip_id).all()
    total_spent = sum(float(e.amount) for e in expenses)
    budget_total = float(trip.budget_total)
    remaining = budget_total - total_spent
    percent_spent = round((total_spent / budget_total) * 100, 2) if budget_total > 0 else 0.0

    # Calculate days
    start_d = trip.start_date if isinstance(trip.start_date, date) else datetime.strptime(str(trip.start_date), "%Y-%m-%d").date()
    end_d = trip.end_date if isinstance(trip.end_date, date) else datetime.strptime(str(trip.end_date), "%Y-%m-%d").date()
    num_days = max(1, (end_d - start_d).days + 1)
    daily_budget = round(budget_total / num_days, 2)

    # Today's spending
    today = date.today()
    today_expenses = [e for e in expenses if e.logged_at and e.logged_at.date() == today]
    daily_spent = sum(float(e.amount) for e in today_expenses)
    daily_remaining = round(daily_budget - daily_spent, 2)

    # Category breakdown
    cat_breakdown: Dict[str, float] = {}
    for e in expenses:
        cat = e.category.lower()
        cat_breakdown[cat] = round(cat_breakdown.get(cat, 0.0) + float(e.amount), 2)

    return TripBudgetSummaryResponse(
        trip_id=trip.id,
        destination=trip.destination,
        budget_total=budget_total,
        spent=round(total_spent, 2),
        remaining=round(remaining, 2),
        percent_spent=percent_spent,
        daily_budget=daily_budget,
        daily_spent=round(daily_spent, 2),
        daily_remaining=daily_remaining,
        category_breakdown=cat_breakdown
    )
