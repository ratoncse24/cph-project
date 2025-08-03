from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from contextlib import asynccontextmanager
from typing import Dict, List, Any
import asyncio
from app.api import api_router_v1
from app.core.config import settings
from app.core.logger import logger
from app.core.middleware import setup_security_middleware
from app.core.exceptions import (
    APIException,
    api_exception_handler,
    validation_exception_handler,
    pydantic_validation_exception_handler,
    general_exception_handler
)
# SQS Event Processing imports
from app.events.sqs_consumer import SQSConsumerService

# Global SQS consumer instance
sqs_consumer_service = None
sqs_consumer_task = None

async def initialize_sqs_consumer():
    """Initialize and start SQS consumer with event handlers"""
    global sqs_consumer_service, sqs_consumer_task
    
    try:
        logger.info("🎯 Initializing SQS event processing with direct routing")

        # Create and start SQS consumer
        sqs_consumer_service = SQSConsumerService()
        
        # Start consumer as background task using the correct method
        queue_url = getattr(settings, 'AWS_SQS_INCOMING_EVENTS_QUEUE_URL', None)
        if queue_url:
            sqs_consumer_task = asyncio.create_task(
                sqs_consumer_service.start_background_consumer(
                    queue_url=queue_url,
                    max_messages=10,
                    wait_time_seconds=5
                )
            )
            logger.info("🚀 SQS Consumer started successfully")
        else:
            logger.warning("⚠️  SQS queue URL not configured. SQS consumer will not start.")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize SQS consumer: {e}")
        raise

async def shutdown_sqs_consumer():
    """Gracefully shutdown SQS consumer"""
    global sqs_consumer_service, sqs_consumer_task
    
    try:
        if sqs_consumer_task and not sqs_consumer_task.done():
            logger.info("🛑 Shutting down SQS consumer...")
            sqs_consumer_task.cancel()
            
            try:
                await sqs_consumer_task
            except asyncio.CancelledError:
                logger.info("✅ SQS consumer task cancelled")
            
        if sqs_consumer_service:
            logger.info("✅ SQS consumer service stopped")
            
    except Exception as e:
        logger.error(f"❌ Error shutting down SQS consumer: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events
    """
    # Startup
    logger.info(f"🚀 Starting {settings.PROJECT_NAME} API")

    logger.info(f"📍 Environment: {settings.ENVIRONMENT}")
    logger.info(f"🐛 Debug mode: {settings.DEBUG}")
    
    # Validate configuration on startup
    try:
        settings.validate_environment()
        logger.info("✅ Configuration validation passed")
    except ValueError as e:
        logger.error(f"❌ Configuration validation failed: {e}")
        raise e
    
    # Initialize SQS consumer
    await initialize_sqs_consumer()
    
    yield
    
    # Shutdown
    await shutdown_sqs_consumer()
    logger.info("🛑 Shutting down User Management API")


# Initialize the FastAPI application with enhanced configuration
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.DESCRIPTION,
    version=settings.VERSION,
    docs_url="/docs" if settings.docs_enabled else None,
    redoc_url="/redoc" if settings.docs_enabled else None,
    openapi_url="/openapi.json" if settings.docs_enabled else None,
    lifespan=lifespan,
    # Add OpenAPI security scheme for Swagger UI
    openapi_extra={
        "components": {
            "securitySchemes": {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "description": "Enter your JWT access token"
                }
            }
        },
        "security": [{"BearerAuth": []}]
    }
)


# Unified Exception Handlers using ResponseFormatter
@app.exception_handler(APIException)
async def handle_api_exception(request: Request, exc: APIException):
    return await api_exception_handler(request, exc)


@app.exception_handler(RequestValidationError) 
async def handle_validation_exception(request: Request, exc: RequestValidationError):
    return await validation_exception_handler(request, exc)


@app.exception_handler(ValidationError)
async def handle_pydantic_validation_exception(request: Request, exc: ValidationError):
    return await pydantic_validation_exception_handler(request, exc)


@app.exception_handler(Exception)
async def handle_general_exception(request: Request, exc: Exception):
    return await general_exception_handler(request, exc)


# Setup security middleware (order matters!)
setup_security_middleware(app)

# Standard CORS middleware (after security middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.ALLOW_CREDENTIALS,
    allow_methods=settings.ALLOWED_METHODS,
    allow_headers=settings.ALLOWED_HEADERS,
)

# Include API routers
app.include_router(api_router_v1, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    """
    Root endpoint with API information
    """
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT.value,
        "docs_url": "/docs" if settings.docs_enabled else "Documentation disabled in production"
    }


@app.get("/health")
async def health_check():
    """
    Basic health check endpoint
    """
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT.value
    }
