from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import uuid
from jose import JWTError, jwt, ExpiredSignatureError
from passlib.context import CryptContext
from fastapi import HTTPException, status
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenError(Exception):
    """Custom token error class"""
    pass


class ExpiredTokenError(TokenError):
    """Token has expired"""
    pass


class InvalidTokenError(TokenError):
    """Token is invalid"""
    pass


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token with enhanced security features
    
    Args:
        data: Payload data to encode
        expires_delta: Optional custom expiration time
        
    Returns:
        JWT token string
    """
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Add standard JWT claims
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),  # Issued at
        "jti": str(uuid.uuid4()),  # JWT ID for tracking
        "type": "access"  # Token type
    })
    
    try:
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    except Exception as e:
        raise TokenError(f"Failed to create access token: {str(e)}")


def create_refresh_token(data: dict) -> str:
    """
    Create a JWT refresh token with longer expiration
    
    Args:
        data: Payload data to encode
        
    Returns:
        JWT refresh token string
    """
    to_encode = data.copy()
    
    # Set longer expiration for refresh tokens
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    # Add standard JWT claims
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": str(uuid.uuid4()),
        "type": "refresh"  # Mark as refresh token
    })
    
    try:
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)
        return encoded_jwt
    except Exception as e:
        raise TokenError(f"Failed to create refresh token: {str(e)}")


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate JWT access token with enhanced error handling
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded payload or None if invalid
        
    Raises:
        ExpiredTokenError: If token has expired
        InvalidTokenError: If token is invalid
    """
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": True, "verify_iat": True}
        )
        
        # Validate token type
        if payload.get("type") != "access":
            raise InvalidTokenError("Invalid token type")
            
        # Validate required claims
        required_claims = ["sub", "exp", "iat", "jti"]
        for claim in required_claims:
            if claim not in payload:
                raise InvalidTokenError(f"Missing required claim: {claim}")
        
        return payload
        
    except ExpiredSignatureError:
        raise ExpiredTokenError("Token has expired")
    except JWTError as e:
        raise InvalidTokenError(f"Invalid token: {str(e)}")
    except Exception as e:
        raise InvalidTokenError(f"Token validation failed: {str(e)}")


def decode_refresh_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate JWT refresh token
    
    Args:
        token: JWT refresh token string
        
    Returns:
        Decoded payload or None if invalid
        
    Raises:
        ExpiredTokenError: If token has expired
        InvalidTokenError: If token is invalid
    """
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": True, "verify_iat": True}
        )
        
        # Validate token type
        if payload.get("type") != "refresh":
            raise InvalidTokenError("Invalid token type")
            
        # Validate required claims
        required_claims = ["sub", "exp", "iat", "jti"]
        for claim in required_claims:
            if claim not in payload:
                raise InvalidTokenError(f"Missing required claim: {claim}")
        
        return payload
        
    except ExpiredSignatureError:
        raise ExpiredTokenError("Refresh token has expired")
    except JWTError as e:
        raise InvalidTokenError(f"Invalid refresh token: {str(e)}")
    except Exception as e:
        raise InvalidTokenError(f"Refresh token validation failed: {str(e)}")


def create_token_pair(data: dict) -> Dict[str, str]:
    """
    Create both access and refresh tokens
    
    Args:
        data: Payload data to encode
        
    Returns:
        Dictionary containing both tokens
    """
    access_token = create_access_token(data)
    refresh_token = create_refresh_token(data)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


async def refresh_access_token(refresh_token: str, db=None) -> Dict[str, str]:
    """
    Create new access token from refresh token
    
    Args:
        refresh_token: Valid refresh token
        db: Database session for token version validation
        
    Returns:
        New token pair
        
    Raises:
        HTTPException: If refresh token is invalid
    """
    try:
        payload = decode_refresh_token(refresh_token)
        
        # Ensure payload is valid
        if payload is None:
            raise InvalidTokenError("Invalid refresh token payload")
        
        # Validate token version if database is provided
        if db is not None:
            from app.repository.user import get_user_by_username
            username = payload.get("sub")
            if username:
                user = await get_user_by_username(db, username)
                if user:
                    token_version = payload.get("token_version")
                    user_token_version = getattr(user, 'token_version', 0)
                    
                    if token_version is not None and token_version != user_token_version:
                        raise InvalidTokenError("Token has been invalidated due to password change")
            
        # Create new token pair with same user data (preserve additional claims)
        user_data = {
            "sub": payload["sub"],  # This will be the username
            "user_id": payload.get("user_id"),
            "username": payload.get("username"),
            "token_version": payload.get("token_version")  # Include token version
        }
        # Add email if it exists in the original token
        if payload.get("email"):
            user_data["email"] = payload.get("email")
        
        # Remove None values
        user_data = {k: v for k, v in user_data.items() if v is not None}
        return create_token_pair(user_data)
        
    except ExpiredTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has expired",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )


def get_token_jti(token: str) -> Optional[str]:
    """
    Extract JWT ID from token without full validation
    
    Args:
        token: JWT token string
        
    Returns:
        JWT ID or None if not found
    """
    try:
        # Decode without verification to get JTI
        payload = jwt.decode(
            token,
            key="dummy",  # Dummy key since we're not verifying signature 
            algorithms=[settings.ALGORITHM],
            options={"verify_signature": False, "verify_exp": False}
        )
        return payload.get("jti")
    except:
        return None


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed)


def validate_token_structure(token: str) -> bool:
    """
    Validate basic token structure without signature verification
    
    Args:
        token: JWT token string
        
    Returns:
        True if structure is valid
    """
    try:
        # Split token parts
        parts = token.split('.')
        if len(parts) != 3:
            return False
            
        # Decode header and payload without verification
        jwt.decode(
            token, 
            key="dummy",  # Dummy key since we're not verifying signature
            algorithms=[settings.ALGORITHM],
            options={"verify_signature": False}
        )
        return True
    except:
        return False
