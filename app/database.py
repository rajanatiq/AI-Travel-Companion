from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Create SQLAlchemy engine for SQL Server
engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    fast_executemany=True
)

# SQLite Engine (For Render/Online Demo)
# engine = create_engine(
#     settings.DATABASE_URL,
#     echo=False,
#     connect_args={"check_same_thread": False}
# )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db() -> Session:
    """FastAPI Dependency to yield a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def test_connection() -> bool:
    """Helper to test database connectivity."""
    try:
        with engine.connect() as connection:
            logger.info("Successfully connected to database.")
            return True
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return False
