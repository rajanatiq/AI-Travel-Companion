from app.database import engine, Base
from app.models import Trip, CityImageCache, VerifiedPlaceCache
from sqlalchemy import text

# Create new tables
Base.metadata.create_all(bind=engine)

# Alter existing trip table
try:
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE trips ADD cover_photo NVARCHAR(512) NULL"))
        print("Added cover_photo to trips table")
except Exception as e:
    print("Could not add cover_photo (might already exist):", e)
