# config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List
from enum import Enum


class Environment(str, Enum):
    """Application environment enumeration"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    # Environment Configuration
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    DEBUG: bool = True  # Default True for development
    
    # Database Configuration
    POSTGRES_DB: str = "fastapi_db"
    POSTGRES_USER: str = "admin"  
    POSTGRES_PASSWORD: str = "admin"
    DATABASE_URL: str = "postgresql+asyncpg://admin:admin@host.docker.internal:5432/fastapi_db"
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_ECHO: bool = False  # Set to True for SQL logging in development
    
    # Security Configuration
    JWT_SECRET_KEY: str = "your-jwt-secret-key-change-in-production"
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    
    # API Configuration
    API_V1_PREFIX: str = "/projects/api/v1"
    PROJECT_NAME: str = "Model Management API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "A robust FastAPI application for user management"
    
    # CORS Configuration
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",  # React default
        "http://localhost:8000",  # FastAPI default
        "http://localhost:8080",  # Vue default
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8080"
    ]
    ALLOWED_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
    ALLOWED_HEADERS: List[str] = ["*"]
    ALLOW_CREDENTIALS: bool = True

    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: str = "logs/app.log"
    LOG_ROTATION: str = "daily"
    LOG_RETENTION: int = 7  # days
    
    # AWS Configuration
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_S3_BUCKET_NAME: Optional[str] = None
    
    # AWS SQS Configuration for incoming events
    AWS_SQS_INCOMING_EVENTS_QUEUE_URL: Optional[str] = None
    
    # AWS SNS Configuration for outgoing events
    AWS_SNS_EVENTS_TOPIC_ARN: Optional[str] = None
    
    # Email Configuration (optional)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_USE_TLS: bool = True
    EMAIL_FROM: Optional[str] = None

    # SMS Configuration
    SMS_PROVIDER: str = "twilio"
    SMS_ACCOUNT_SID: Optional[str] = None
    SMS_AUTH_TOKEN: Optional[str] = None
    SMS_FROM_NUMBER: Optional[str] = None
    SMS_ENABLED: bool = False
    
    # File Upload Configuration
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_FILE_TYPES: List[str] = [".jpg", ".jpeg", ".png", ".pdf", ".txt"]
    UPLOAD_PATH: str = "uploads"
    
    # Pagination Configuration
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"  # Ignore extra environment variables
    )
    
    # Environment-specific property methods
    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.ENVIRONMENT == Environment.DEVELOPMENT
    
    @property
    def is_staging(self) -> bool:
        """Check if running in staging environment"""
        return self.ENVIRONMENT == Environment.STAGING
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.ENVIRONMENT == Environment.PRODUCTION
    
    @property
    def docs_enabled(self) -> bool:
        """Enable docs only in development and staging"""
        return not self.is_production
    
    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL (for Alembic)"""
        return self.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    
    @property
    def cors_origins(self) -> List[str]:
        """Get CORS origins based on environment"""
        if self.is_development:
            return self.ALLOWED_ORIGINS + ["*"]  # Allow all in development
        return self.ALLOWED_ORIGINS
    
    def get_database_url(self, async_driver: bool = True) -> str:
        """Get database URL with optional async driver"""
        if async_driver:
            return self.DATABASE_URL
        return self.database_url_sync
    
    def validate_environment(self) -> bool:
        """Validate environment-specific requirements"""
        if self.is_production:
            # Production validation
            if self.JWT_SECRET_KEY == "your-jwt-secret-key-change-in-production":
                raise ValueError("JWT_SECRET_KEY must be changed in production")
            if self.SECRET_KEY == "your-secret-key-change-in-production":
                raise ValueError("SECRET_KEY must be changed in production")
            if self.DEBUG:
                raise ValueError("DEBUG must be False in production")
        
        return True


# Create settings instance
settings = Settings()

# Validate settings on import (only if not in testing)
import os
if not os.getenv("TESTING"):
    settings.validate_environment()
