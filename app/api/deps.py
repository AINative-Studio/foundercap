"""Dependency injection for FastAPI routes."""
from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.redis import get_redis
from app.db.session import SessionLocal
from app.schemas.token import TokenPayload

# OAuth2 scheme for token authentication
security = HTTPBearer()


def get_db() -> Generator[Session, None, None]:
    """Get a database session.
    
    Yields:
        Session: Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Reuse the database session in the path operation functions
DatabaseSession = Depends(get_db)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = DatabaseSession,
) -> TokenPayload:
    """Get the current user from the token.
    
    Args:
        credentials: HTTP Authorization credentials
        db: Database session
        
    Returns:
        TokenPayload: Decoded token payload
        
    Raises:
        HTTPException: If the token is invalid or the user doesn't exist
    """
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
        token_data = TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise credentials_exception
    
    # Here you would typically fetch the user from the database
    # user = crud.user.get(db, id=token_data.sub)
    # if user is None:
    #     raise credentials_exception
    # return user
    
    # For now, just return the token data
    return token_data


# Dependencies for different permission levels
def get_current_active_user(
    current_user: TokenPayload = Depends(get_current_user),
) -> TokenPayload:
    """Get the current active user.
    
    Args:
        current_user: Current user from token
        
    Returns:
        TokenPayload: Current user
        
    Raises:
        HTTPException: If the user is inactive
    """
    # if not current_user.is_active:
    #     raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def get_current_active_superuser(
    current_user: TokenPayload = Depends(get_current_user),
) -> TokenPayload:
    """Get the current active superuser.
    
    Args:
        current_user: Current user from token
        
    Returns:
        TokenPayload: Current superuser
        
    Raises:
        HTTPException: If the user is not a superuser
    """
    # if not current_user.is_superuser:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="The user doesn't have enough privileges",
    #     )
    return current_user


# Redis dependency
def get_redis_client():
    """Get Redis client.
    
    Returns:
        Redis: Redis client instance
    """
    return get_redis()


# Common dependencies
RedisClient = Depends(get_redis_client)
