import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Preferences
from app.schemas import (
    UserRegisterRequest, UserLoginRequest, UserResponse,
    TokenResponse, RefreshTokenRequest, PreferencesUpdate, PreferencesResponse,
    UserProfileUpdateRequest
)
from app.security import (
    hash_password, verify_password, create_access_token,
    create_refresh_token, decode_token, get_current_user
)

router = APIRouter(prefix="/auth", tags=["Authentication & Profile"])

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(req: UserRegisterRequest, db: Session = Depends(get_db)):
    """Register a new user account and initialize default preferences."""
    existing_user = db.query(User).filter(User.email == req.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists"
        )
    
    new_user = User(
        id=uuid.uuid4(),
        email=req.email,
        password_hash=hash_password(req.password),
        home_locale=req.home_locale or "en",
        full_name=req.full_name,
        phone_number=req.phone_number,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(new_user)
    db.flush()

    user_prefs = Preferences(
        user_id=new_user.id,
        interests=["food", "history", "culture"],
        pace_preference="balanced",
        default_budget_tier=2,
        updated_at=datetime.now(timezone.utc)
    )
    db.add(user_prefs)
    db.commit()
    db.refresh(new_user)

    access_token = create_access_token(str(new_user.id), new_user.email)
    refresh_token = create_refresh_token(str(new_user.id), new_user.email)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=new_user
    )

@router.post("/login", response_model=TokenResponse)
def login(req: UserLoginRequest, db: Session = Depends(get_db)):
    """Authenticate user credentials and issue JWT tokens."""
    user = db.query(User).filter(User.email == req.email).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    access_token = create_access_token(str(user.id), user.email)
    refresh_token = create_refresh_token(str(user.id), user.email)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=user
    )

@router.post("/refresh", response_model=TokenResponse)
def refresh_token(req: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Refresh an expired access token using a valid refresh token."""
    token_data = decode_token(req.refresh_token)
    if not token_data or token_data.type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    if token_data.exp < datetime.now(timezone.utc).timestamp():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired. Please login again"
        )
    
    try:
        user_uuid = uuid.UUID(token_data.sub)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")
    
    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    new_access_token = create_access_token(str(user.id), user.email)
    new_refresh_token = create_refresh_token(str(user.id), user.email)

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        user=user
    )

@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Return the full profile and preferences of the currently logged-in user."""
    return current_user

@router.put("/profile", response_model=UserResponse)
def update_user_profile(
    profile_in: UserProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user personal details (full_name, phone_number, age, country, city, bio)."""
    if profile_in.full_name is not None:
        current_user.full_name = profile_in.full_name
    if profile_in.phone_number is not None:
        current_user.phone_number = profile_in.phone_number
    if profile_in.age is not None:
        current_user.age = profile_in.age
    if profile_in.country is not None:
        current_user.country = profile_in.country
    if profile_in.city is not None:
        current_user.city = profile_in.city
    if profile_in.bio is not None:
        current_user.bio = profile_in.bio
    if profile_in.avatar_url is not None:
        current_user.avatar_url = profile_in.avatar_url
    if profile_in.home_locale is not None:
        current_user.home_locale = profile_in.home_locale
        
    current_user.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(current_user)
    return current_user

@router.put("/preferences", response_model=PreferencesResponse)
def update_preferences(
    prefs_in: PreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user travel preferences (interests, pace, budget tier)."""
    prefs = db.query(Preferences).filter(Preferences.user_id == current_user.id).first()
    if not prefs:
        prefs = Preferences(user_id=current_user.id)
        db.add(prefs)
    
    prefs.interests = prefs_in.interests
    prefs.pace_preference = prefs_in.pace_preference
    prefs.default_budget_tier = prefs_in.default_budget_tier
    prefs.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(prefs)
    return prefs
