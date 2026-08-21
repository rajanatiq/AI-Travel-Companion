from app.database import engine
from sqlalchemy import text

try:
    with engine.connect() as conn:
        result = conn.execute(text("SELECT cover_photo FROM trips")).fetchall()
        print(f"Success! Found cover_photo column. Number of rows: {len(result)}")
except Exception as e:
    print(f"Error querying trips table: {e}")
