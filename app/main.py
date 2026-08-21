import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import test_connection
from app.routes import auth, trips, itinerary, expenses, places, discovery

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"
)
logger = logging.getLogger("ai_travel_backend")

from app.database import engine, Base

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} ({settings.ENVIRONMENT})")
    try:
        # Create tables automatically for SQLite
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully.")
    except Exception as e:
        logger.warning(f"Could not create database tables: {e}")
        
    is_connected = test_connection()
    if is_connected:
        logger.info("Database is ready and operational.")
    else:
        logger.warning("Could not establish immediate DB connection.")
    yield
    logger.info("Shutting down AI Travel Companion backend...")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    ### AI Travel Companion — High Performance REST Backend
    Production-grade API for itinerary planning, external POI scoring, expense tracking, and offline synchronization.
    """,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for frontend and mobile apps
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API v1 Routes
api_prefix = "/api/v1"
app.include_router(auth.router, prefix=api_prefix)
app.include_router(trips.router, prefix=api_prefix)
app.include_router(itinerary.router, prefix=api_prefix)
app.include_router(expenses.router, prefix=api_prefix)
app.include_router(places.router, prefix=api_prefix)
app.include_router(discovery.router, prefix=api_prefix)

# Root and Health Check
@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT
    }

@app.get("/", tags=["Health"])
def root():
    return {
        "message": "Welcome to the AI Travel Companion API!",
        "documentation": "/docs",
        "health": "/health",
        "status": "active"
    }
