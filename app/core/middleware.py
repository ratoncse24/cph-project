import time
import uuid
from typing import Callable, Dict, Any
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all responses
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Security Headers
        security_headers = {
            # Prevent clickjacking attacks
            "X-Frame-Options": "DENY",
            
            # Prevent MIME type sniffing
            "X-Content-Type-Options": "nosniff",
            
            # Enable XSS protection
            "X-XSS-Protection": "1; mode=block",
            
            # Referrer Policy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # Strict Transport Security (HTTPS only)
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
            
            # Permissions Policy
            "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
            
            # Remove server information
            "Server": settings.PROJECT_NAME,
        }
        
        # Environment-specific Content Security Policy
        if settings.is_development:
            # More permissive CSP for development (allows Swagger UI)
            security_headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://unpkg.com; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com; "
                "img-src 'self' data: https:; "
                "font-src 'self' https://cdn.jsdelivr.net; "
                "connect-src 'self'; "
                "object-src 'none';"
            )
        else:
            # Strict CSP for production
            security_headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self'; "
                "object-src 'none'; "
                "frame-ancestors 'none';"
            )
        
        # Apply security headers
        for header, value in security_headers.items():
            response.headers[header] = value
        
        return response


class RequestTrackingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track and log requests with unique IDs
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        # Log request start
        start_time = time.time()
        client_ip = self.get_client_ip(request)
        
        logger.info(
            f"Request started - ID: {request_id}, Method: {request.method}, "
            f"URL: {request.url}, IP: {client_ip}, User-Agent: {request.headers.get('user-agent', 'Unknown')}"
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(round(process_time, 4))
            
            # Log request completion
            logger.info(
                f"Request completed - ID: {request_id}, Status: {response.status_code}, "
                f"Process time: {round(process_time, 4)}s"
            )
            
            return response
            
        except Exception as e:
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log request error
            logger.error(
                f"Request failed - ID: {request_id}, Error: {str(e)}, "
                f"Process time: {round(process_time, 4)}s"
            )
            
            # Return error response with request ID
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error", "request_id": request_id},
                headers={"X-Request-ID": request_id}
            )
    
    def get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request"""
        # Check for forwarded headers (when behind proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        return request.client.host if request.client else "unknown"


class RequestSizeMiddleware(BaseHTTPMiddleware):
    """
    Middleware to limit request body size
    """
    
    def __init__(self, app: ASGIApp, max_size: int = 10 * 1024 * 1024):  # 10MB default
        super().__init__(app)
        self.max_size = max_size
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Check Content-Length header
        content_length = request.headers.get("content-length")
        
        if content_length:
            try:
                content_length = int(content_length)
                if content_length > self.max_size:
                    return JSONResponse(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content={
                            "detail": f"Request entity too large. Maximum allowed size is {self.max_size} bytes."
                        }
                    )
            except ValueError:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "Invalid Content-Length header"}
                )
        
        return await call_next(request)


class SecurityValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for additional security validations
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.suspicious_patterns = [
            # SQL injection patterns
            "union select", "drop table", "delete from", "insert into",
            # XSS patterns
            "<script", "javascript:", "onload=", "onerror=",
            # Path traversal
            "../", "..\\", "/etc/passwd", "/etc/shadow"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip security validation for documentation endpoints in development
        if settings.is_development and (
            request.url.path.startswith("/docs") or 
            request.url.path.startswith("/redoc") or 
            request.url.path.startswith("/openapi.json")
        ):
            return await call_next(request)
        
        # Validate URL path
        if self.contains_suspicious_patterns(str(request.url).lower()):
            logger.warning(f"Suspicious URL detected: {request.url}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Invalid request"}
            )
        
        # Validate query parameters
        for key, value in request.query_params.items():
            if self.contains_suspicious_patterns(f"{key}={value}".lower()):
                logger.warning(f"Suspicious query parameter detected: {key}={value}")
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "Invalid request parameters"}
                )
        
        # Validate User-Agent header (more lenient in development)
        user_agent = request.headers.get("user-agent", "")
        if not settings.is_development and self.is_suspicious_user_agent(user_agent):
            logger.warning(f"Suspicious User-Agent detected: {user_agent}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Invalid request"}
            )
        
        return await call_next(request)
    
    def contains_suspicious_patterns(self, text: str) -> bool:
        """Check if text contains suspicious patterns"""
        return any(pattern in text for pattern in self.suspicious_patterns)
    
    def is_suspicious_user_agent(self, user_agent: str) -> bool:
        """Check if User-Agent looks suspicious"""
        if not user_agent:
            return True  # Empty or missing User-Agent
        
        suspicious_agents = [
            "sqlmap", "nikto", "nmap", "masscan", "zap", "burp",
            "python-requests", "curl", "wget"  # Be careful with these in production
        ]
        
        return any(agent in user_agent.lower() for agent in suspicious_agents)


class CORSSecurityMiddleware(BaseHTTPMiddleware):
    """
    Enhanced CORS middleware with additional security checks
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        origin = request.headers.get("origin")
        
        # Only validate origins for actual browser requests (those with Origin header)
        # Direct API calls (curl, postman, etc.) don't typically have Origin headers
        if origin:
            # Check if this is a preflight request
            if request.method == "OPTIONS":
                # Handle preflight requests
                if not self.is_origin_allowed(origin):
                    logger.warning(f"Blocked preflight request from unauthorized origin: {origin}")
                    return JSONResponse(
                        status_code=status.HTTP_403_FORBIDDEN,
                        content={"detail": "Origin not allowed"}
                    )
                
                # Return preflight response
                return JSONResponse(
                    content={},
                    headers={
                        "Access-Control-Allow-Origin": origin,
                        "Access-Control-Allow-Credentials": "true",
                        "Access-Control-Allow-Methods": ", ".join(settings.ALLOWED_METHODS),
                        "Access-Control-Allow-Headers": ", ".join(settings.ALLOWED_HEADERS),
                        "Access-Control-Max-Age": "86400"
                    }
                )
            
            # For actual requests with origin, validate only in production
            elif not settings.is_development and not self.is_origin_allowed(origin):
                logger.warning(f"Blocked request from unauthorized origin: {origin}")
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"detail": "Origin not allowed"}
                )
        
        # Process the request
        response = await call_next(request)
        
        # Add CORS headers for allowed origins (only if origin exists)
        if origin and self.is_origin_allowed(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = ", ".join(settings.ALLOWED_METHODS)
            response.headers["Access-Control-Allow-Headers"] = ", ".join(settings.ALLOWED_HEADERS)
            response.headers["Access-Control-Max-Age"] = "86400"  # 24 hours
        
        return response
    
    def is_origin_allowed(self, origin: str) -> bool:
        """Check if origin is in allowed list"""
        if settings.is_development:
            # In development, be more permissive
            return True
        
        return origin in settings.ALLOWED_ORIGINS


class RateLimitInfo:
    """Information about rate limiting"""
    def __init__(self, limit: int, remaining: int, reset_time: int):
        self.limit = limit
        self.remaining = remaining
        self.reset_time = reset_time


def setup_security_middleware(app):
    """
    Setup all security middleware in the correct order
    
    Args:
        app: FastAPI application instance
    """
    # Order matters - more specific middleware should be added first
    
    # 1. Request size validation (first to reject large requests early)
    app.add_middleware(RequestSizeMiddleware, max_size=settings.MAX_FILE_SIZE)
    
    # 2. Security validation (check for malicious patterns)
    app.add_middleware(SecurityValidationMiddleware)
    
    # 3. Request tracking (for logging and monitoring)
    app.add_middleware(RequestTrackingMiddleware)
    
    # 4. CORS security (handle cross-origin requests)
    app.add_middleware(CORSSecurityMiddleware)
    
    # 5. Security headers (last to ensure they're added to all responses)
    app.add_middleware(SecurityHeadersMiddleware)
    
    logger.info("Security middleware setup completed") 