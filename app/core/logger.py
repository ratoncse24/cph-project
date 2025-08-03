import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from app.core.config import settings


def setup_logging():
    """Set up logging configuration based on environment settings"""
    
    # Ensure logs directory exists
    log_file_path = Path(settings.LOG_FILE)
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Get the app logger
    logger = logging.getLogger("app")
    
    # Set log level from configuration
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)
    logger.propagate = False  # Isolate the app logger
    
    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create formatter from configuration
    formatter = logging.Formatter(settings.LOG_FORMAT)
    
    # File handler with rotation
    if settings.LOG_ROTATION.lower() == "daily":
        when = "D"
        interval = 1
    elif settings.LOG_ROTATION.lower() == "weekly":
        when = "W0"  # Weekly on Monday
        interval = 1
    elif settings.LOG_ROTATION.lower() == "monthly":
        when = "D"
        interval = 30
    else:
        when = "D"  # Default to daily
        interval = 1
    
    file_handler = TimedRotatingFileHandler(
        filename=settings.LOG_FILE,
        when=when,
        interval=interval,
        backupCount=settings.LOG_RETENTION,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler - always show INFO and above in console for development
    console_handler = logging.StreamHandler(sys.stdout)
    
    # In production, only show WARNING and above in console
    if settings.is_production:
        console_handler.setLevel(logging.WARNING)
    else:
        console_handler.setLevel(logging.INFO)
    
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Configure other loggers based on environment
    configure_third_party_loggers()
    
    return logger


def configure_third_party_loggers():
    """Configure third-party library loggers"""
    
    # SQLAlchemy logger
    sqlalchemy_logger = logging.getLogger("sqlalchemy")
    if settings.DATABASE_ECHO or settings.LOG_LEVEL.upper() == "DEBUG":
        sqlalchemy_logger.setLevel(logging.INFO)
    else:
        sqlalchemy_logger.setLevel(logging.WARNING)
    sqlalchemy_logger.propagate = False
    
    # FastAPI/Uvicorn loggers
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    
    if settings.is_development:
        uvicorn_logger.setLevel(logging.INFO)
        uvicorn_access_logger.setLevel(logging.INFO)
    else:
        uvicorn_logger.setLevel(logging.WARNING)
        uvicorn_access_logger.setLevel(logging.WARNING)
    
    # AWS/Boto3 loggers (reduce noise)
    boto_loggers = ["boto3", "botocore", "s3transfer", "urllib3"]
    for logger_name in boto_loggers:
        boto_logger = logging.getLogger(logger_name)
        boto_logger.setLevel(logging.WARNING)
        boto_logger.propagate = False


def get_logger(name: str = "app") -> logging.Logger:
    """Get a logger instance with the specified name"""
    return logging.getLogger(name)


# Initialize logging when module is imported
logger = setup_logging()

# Log the configuration
logger.info(f"Logging initialized - Level: {settings.LOG_LEVEL}, File: {settings.LOG_FILE}")
logger.info(f"Environment: {settings.ENVIRONMENT}, Debug: {settings.DEBUG}")

# Export the logger for backward compatibility
__all__ = ["logger", "get_logger", "setup_logging"]
