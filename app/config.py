from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    # App Information
    APP_NAME: str = "AI Travel Companion API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"
    
    # Server Binding
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # SQL Server Database Connection
    DATABASE_URL: str = (
        "mssql+pyodbc://localhost\\SQLEXPRESS/AITravelCompanionDB"
        "?driver=ODBC+Driver+18+for+SQL+Server&trusted_connection=yes&TrustServerCertificate=yes"
    )
    
    # JWT Authentication
    SECRET_KEY: str = "ai-travel-companion-super-secret-key-2026-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 Hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # External APIs (Optional)
    GOOGLE_PLACES_API_KEY: Optional[str] = ""
    OPENWEATHERMAP_API_KEY: Optional[str] = ""
    GEMINI_API_KEY: Optional[str] = ""
    TICKETMASTER_API_KEY: Optional[str] = ""
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
