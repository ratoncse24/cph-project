from typing import Dict, List, Any


def transform_validation_errors(errors: Any) -> Dict[str, List[str]]:
    """
    Transform Pydantic validation errors to Django-like format
    
    Args:
        errors: List of Pydantic validation error dictionaries
        
    Returns:
        Dictionary with field names as keys and error messages as values
    """
    formatted_errors = {}
    
    for error in errors:
        # Get field location - skip 'body' prefix for request body fields
        location = error.get("loc", [])
        if location and location[0] == "body":
            field_path = ".".join(str(loc) for loc in location[1:])
        else:
            field_path = ".".join(str(loc) for loc in location)
        
        # Use 'non_field_errors' for general errors
        field_name = field_path if field_path else "non_field_errors"
        
        # Get error message
        message = error.get("msg", "Invalid value")
        
        # Format specific error types for better readability
        error_type = error.get("type", "")
        if error_type == "string_too_short":
            ctx = error.get("ctx", {})
            min_length = ctx.get("min_length", "required length")
            message = f"This field must have at least {min_length} characters."
        elif error_type == "string_too_long":
            ctx = error.get("ctx", {})
            max_length = ctx.get("max_length", "allowed length")
            message = f"This field must have no more than {max_length} characters."
        elif error_type == "missing":
            message = "This field is required."
        elif error_type == "value_error":
            message = error.get("msg", "Invalid value.")
        elif error_type == "type_error":
            expected_type = error.get("ctx", {}).get("expected_type", "valid type")
            message = f"Invalid input type. Expected {expected_type}."
        elif error_type == "email":
            message = "Enter a valid email address."
        
        # Add to formatted errors
        if field_name not in formatted_errors:
            formatted_errors[field_name] = []
        formatted_errors[field_name].append(message)
    
    return formatted_errors


def format_unified_error_response(
    errors: Any = None, 
    message: str = "An error occurred", 
    request_id: str = "unknown"
) -> Dict[str, Any]:
    """
    Create unified error response format
    
    Args:
        errors: Error details (can be dict, string, or None)
        message: General error message
        request_id: Request tracking ID
        
    Returns:
        Unified error response dictionary
    """
    if isinstance(errors, dict):
        # Already in field-error format
        formatted_errors = errors
    elif isinstance(errors, str):
        # Single error message
        formatted_errors = {"non_field_errors": [errors]}
    elif errors is None:
        # Use message as non-field error
        formatted_errors = {"non_field_errors": [message]}
    else:
        # Fallback
        formatted_errors = {"non_field_errors": [str(errors)]}
    
    return {
        "errors": formatted_errors,
        "message": message,
        "request_id": request_id
    } 