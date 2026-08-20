import pytest
import uuid
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.database import Base, get_db
from app.models import User, Preferences, Trip, ItineraryItem, Expense
from app.main import app
from app.security import hash_password, create_access_token

# SQLite In-Memory Database for fast, isolated tests
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def create_test_tables():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session():
    """Creates a new database session for each test function."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI TestClient with overridden get_db dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def test_user(db_session) -> User:
    """Creates and returns a test user with preferences in the test database."""
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email="traveler@example.com",
        password_hash=hash_password("Password123!"),
        home_locale="en",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    db_session.flush()

    prefs = Preferences(
        user_id=user.id,
        interests=["food", "history", "art"],
        pace_preference="balanced",
        default_budget_tier=2,
        updated_at=datetime.now(timezone.utc)
    )
    db_session.add(prefs)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def auth_headers(test_user: User) -> dict:
    """Returns authorization headers with a valid JWT access token for test_user."""
    token = create_access_token(str(test_user.id), test_user.email)
    return {"Authorization": f"Bearer {token}"}
