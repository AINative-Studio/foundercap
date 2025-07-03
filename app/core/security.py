"""Security and authentication utilities."""
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, Union

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.redis import get_redis
from app.db.session import get_db
from app.schemas.token import TokenData, TokenPayload
from app.schemas.user import User

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash.
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password
        
    Returns:
        bool: True if the password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate a password hash.
    
    Args:
        password: Plain text password
        
    Returns:
        str: Hashed password
    """
    return pwd_context.hash(password)


def create_access_token(
    subject: Union[str, Any], 
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[dict] = None
) -> str:
    """Create a JWT access token.
    
    Args:
        subject: Subject of the token (usually user ID)
        expires_delta: Optional timedelta for token expiration
        additional_claims: Additional claims to include in the token
        
    Returns:
        str: Encoded JWT token
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "iat": datetime.now(timezone.utc),
        "jti": secrets.token_urlsafe(32),
    }
    
    if additional_claims:
        to_encode.update(additional_claims)
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm="HS256"
    )
    
    return encoded_jwt


def create_refresh_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT refresh token.
    
    Args:
        subject: Subject of the token (usually user ID)
        expires_delta: Optional timedelta for token expiration
        
    Returns:
        str: Encoded JWT refresh token
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        # Default refresh token expires in 30 days
        expire = datetime.now(timezone.utc) + timedelta(days=30)
    
    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "iat": datetime.now(timezone.utc),
        "jti": secrets.token_urlsafe(32),
        "type": "refresh"
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm="HS256"
    )
    
    return encoded_jwt


def verify_token(token: str) -> TokenPayload:
    """Verify and decode a JWT token.
    
    Args:
        token: JWT token to verify
        
    Returns:
        TokenPayload: Decoded token payload
        
    Raises:
        HTTPException: If the token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=["HS256"]
        )
        
        # Check if token is blacklisted
        redis_client = get_redis()
        if redis_client and redis_client.get(f"blacklist:{token}"):
            raise credentials_exception
            
        token_data = TokenPayload(**payload)
        
        # Convert exp from timestamp to datetime
        if isinstance(token_data.exp, int):
            token_data.exp = datetime.fromtimestamp(token_data.exp, timezone.utc)
        
        # Check if token is expired
        if token_data.exp < datetime.now(timezone.utc):
            raise credentials_exception
            
        return token_data
        
    except (JWTError, ValidationError) as e:
        logger.error(f"Token validation error: {e}")
        raise credentials_exception from e


def blacklist_token(token: str, expires_in: Optional[int] = None) -> None:
    """Add a token to the blacklist.
    
    Args:
        token: Token to blacklist
        expires_in: Optional expiration time in seconds
    """
    if not token:
        return
        
    try:
        # Decode the token to get expiration
        payload = jwt.get_unverified_claims(token)
        exp = payload.get("exp")
        
        # If no expires_in provided, calculate from token expiration
        if expires_in is None and exp:
            now = datetime.now(timezone.utc).timestamp()
            expires_in = int(exp - now)
            if expires_in <= 0:
                return  # Token already expired
        
        # Add to Redis blacklist
        redis_client = get_redis()
        if redis_client and expires_in and expires_in > 0:
            redis_client.set(
                f"blacklist:{token}",
                "1",
                ex=expires_in
            )
            
    except Exception as e:
        logger.error(f"Error blacklisting token: {e}")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Get the current user from the token.
    
    Args:
        token: JWT token from Authorization header
        db: Database session
        
    Returns:
        User: Authenticated user
        
    Raises:
        HTTPException: If the token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = verify_token(token)
        
        # In a real app, you would fetch the user from the database here
        # For now, we'll return a mock user
        # user = crud.user.get(db, id=payload.sub)
        # if user is None:
        #     raise credentials_exception
        # return user
        
        # Mock user for now
        return User(
            id=1,
            email="user@example.com",
            is_active=True,
            is_superuser=False,
            first_name="Test",
            last_name="User",
        )
        
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        raise credentials_exception from e


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get the current active user.
    
    Args:
        current_user: Current user from token
        
    Returns:
        User: Active user
        
    Raises:
        HTTPException: If the user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def get_current_active_superuser(
    current_user: User = Depends(get_current_user,
) -> User:
    """Get the current active superuser.
    
    Args:
        current_user: Current user from token
        
    Returns:
        User: Active superuser
        
    Raises:
        HTTPException: If the user is not a superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user


def generate_password_reset_token(email: str) -> str:
    """Generate a password reset token.
    
    Args:
        email: User's email
        
    Returns:
        str: JWT token for password reset
    """
    delta = timedelta(hours=settings.EMAIL_RESET_TOKEN_EXPIRE_HOURS)
    now = datetime.now(timezone.utc)
    expires = now + delta
    
    to_encode = {
        "exp": expires,
        "sub": email,
        "iat": now,
        "jti": secrets.token_urlsafe(32),
        "type": "reset"
    }
    
    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm="HS256"
    )


def verify_password_reset_token(token: str) -> Optional[str]:
    """Verify a password reset token.
    
    Args:
        token: JWT token to verify
        
    Returns:
        Optional[str]: Email if token is valid, None otherwise
    """
    try:
        payload = verify_token(token)
        if payload.type != "reset":
            return None
        return payload.sub
    except (JWTError, ValidationError):
        return None


def generate_email_verification_token(email: str) -> str:
    """Generate an email verification token.
    
    Args:
        email: User's email
        
    Returns:
        str: JWT token for email verification
    """
    delta = timedelta(hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS)
    now = datetime.now(timezone.utc)
    expires = now + delta
    
    to_encode = {
        "exp": expires,
        "sub": email,
        "iat": now,
        "jti": secrets.token_urlsafe(32),
        "type": "verify"
    }
    
    return jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm="HS256"
    )


def verify_email_verification_token(token: str) -> Optional[str]:
    """Verify an email verification token.
    
    Args:
        token: JWT token to verify
        
    Returns:
        Optional[str]: Email if token is valid, None otherwise
    """
    try:
        payload = verify_token(token)
        if payload.type != "verify":
            return None
        return payload.sub
    except (JWTError, ValidationError):
        return None
