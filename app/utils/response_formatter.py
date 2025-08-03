from typing import Any, List, Optional, Dict, Union
from pydantic import BaseModel, Field
from app.utils.pagination import PaginatedResponse, PaginationMeta


class APIResponse(BaseModel):
    """Standard API response format"""
    success: bool = Field(..., description="Whether the request was successful")
    message: str = Field(default="", description="Response message")
    response: Dict[str, Any] = Field(..., description="Response data")
    errors: Union[List[str], Dict[str, List[str]]] = Field(default_factory=list, description="List of errors or dictionary of field errors")

    def to_dict(self) -> dict:
        """Convert to dictionary with proper JSON serialization"""
        return self.model_dump(mode='json')


class ResponseFormatter:
    """Utility class for formatting API responses consistently"""
    
    @staticmethod
    def success_response(
        data: Any,
        message: str = "Request Successful"
    ) -> APIResponse:
        """
        Create a successful response - automatically handles lists, pagination, and single objects
        
        Args:
            data: The data to return (can be list, PaginatedResponse, or single object)
            message: Success message
            
        Returns:
            Standardized APIResponse
        """
        # Handle paginated response
        if isinstance(data, PaginatedResponse):
            # Convert to dict with proper JSON serialization
            data_dict = data.model_dump(mode='json')
            return APIResponse(
                success=True,
                message=message,
                response={
                    "data": data_dict['results'],
                    "pagination": data_dict['meta']
                },
                errors=[]
            )
        
        # Handle Pydantic models
        elif hasattr(data, 'model_dump'):
            return APIResponse(
                success=True,
                message=message,
                response={
                    "data": data.model_dump(mode='json'),
                    "pagination": {}
                },
                errors=[]
            )
        
        # Handle list of Pydantic models
        elif isinstance(data, list) and data and hasattr(data[0], 'model_dump'):
            return APIResponse(
                success=True,
                message=message,
                response={"data": [item.model_dump(mode='json') for item in data]},
                errors=[]
            )
        
        # Handle regular list response (without pagination)
        elif isinstance(data, list):
            return APIResponse(
                success=True,
                message=message,
                response={"data": data},
                errors=[]
            )
        
        # Handle regular dictionary or primitive data
        else:
            return APIResponse(
                success=True,
                message=message,
                response={
                    "data": data,
                    "pagination": {}
                },
                errors=[]
            )
    
    @staticmethod
    def error_response(
        message: str = "Request Failed",
        errors: Optional[Union[str, List[str], Dict[str, List[str]]]] = None,
        data: Any = None
    ) -> APIResponse:
        """
        Create an error response
        
        Args:
            message: Error message
            errors: Single error string, list of errors, or dictionary of field errors
            data: Optional data to include (usually None for errors)
            
        Returns:
            Standardized APIResponse for errors
        """
        if errors is None:
            processed_errors = []
        elif isinstance(errors, str):
            processed_errors = [errors]
        elif isinstance(errors, dict):
            # Keep dictionary format for structured field errors
            processed_errors = errors
        else:
            # List of strings
            processed_errors = errors
        
        response_data = {"data": data if data is not None else []}
        
        return APIResponse(
            success=False,
            message=message,
            response=response_data,
            errors=processed_errors
        ) 