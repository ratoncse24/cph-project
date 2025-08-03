from typing import Union, List, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from app.utils.response_formatter import ResponseFormatter
from app.core.logger import logger
from app.utils.error_formatters import transform_validation_errors


class APIException(Exception):
    """Base exception for API business logic errors"""
    
    def __init__(
        self,
        message: str = "Request Failed",
        errors: Optional[Union[str, List[str]]] = None,
        status_code: int = 400
    ):
        self.message = message
        self.errors = errors if errors is not None else []
        self.status_code = status_code
        super().__init__(self.message)


class ValidationException(APIException):
    """Exception for validation errors"""
    
    def __init__(
        self,
        message: str = "Validation failed",
        errors: Optional[Union[str, List[str]]] = None
    ):
        super().__init__(message=message, errors=errors, status_code=422)


class BusinessLogicException(APIException):
    """Exception for business logic errors"""
    
    def __init__(
        self,
        message: str = "Business logic error",
        errors: Optional[Union[str, List[str]]] = None,
        status_code: int = 400
    ):
        super().__init__(message=message, errors=errors, status_code=status_code)


class AuthenticationException(APIException):
    """Exception for authentication errors"""
    
    def __init__(
        self,
        message: str = "Authentication failed",
        errors: Optional[Union[str, List[str]]] = None
    ):
        super().__init__(message=message, errors=errors, status_code=401)


class AuthorizationException(APIException):
    """Exception for authorization errors"""
    
    def __init__(
        self,
        message: str = "Access denied",
        errors: Optional[Union[str, List[str]]] = None
    ):
        super().__init__(message=message, errors=errors, status_code=403)


class NotFoundException(APIException):
    """Exception for resource not found errors"""
    
    def __init__(
        self,
        message: str = "Resource not found",
        errors: Optional[Union[str, List[str]]] = None
    ):
        super().__init__(message=message, errors=errors, status_code=404)


class ConflictException(APIException):
    """Exception for resource conflict errors"""
    
    def __init__(
        self,
        message: str = "Resource conflict",
        errors: Optional[Union[str, List[str]]] = None
    ):
        super().__init__(message=message, errors=errors, status_code=409)


# Global Exception Handlers

async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """Handle custom API exceptions"""
    logger.warning(f"API Exception: {exc.message} - {exc.errors}")
    
    response_data = ResponseFormatter.error_response(
        message=exc.message,
        errors=exc.errors
    )
    
    return JSONResponse(
        content=response_data.to_dict(),
        status_code=exc.status_code
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic validation errors"""
    logger.warning(f"Validation Error: {exc.errors()}")
    
    # Use existing transform_validation_errors function for consistent formatting
    formatted_errors = transform_validation_errors(exc.errors())
    
    response_data = ResponseFormatter.error_response(
        message="Validation failed",
        errors=formatted_errors
    )
    
    return JSONResponse(
        content=response_data.to_dict(),
        status_code=422
    )


async def pydantic_validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle Pydantic ValidationError"""
    logger.warning(f"Pydantic Validation Error: {exc.errors()}")
    
    # Use existing transform_validation_errors function for consistent formatting
    formatted_errors = transform_validation_errors(exc.errors())
    
    response_data = ResponseFormatter.error_response(
        message="Validation failed",
        errors=formatted_errors
    )
    
    return JSONResponse(
        content=response_data.to_dict(),
        status_code=422
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions"""
    logger.error(f"Unexpected error: {str(exc)}", exc_info=True)
    
    response_data = ResponseFormatter.error_response(
        message="Internal server error",
        errors="An unexpected error occurred"
    )
    
    return JSONResponse(
        content=response_data.to_dict(),
        status_code=500
    ) 