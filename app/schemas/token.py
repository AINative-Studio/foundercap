"""Token related schemas."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Token(BaseModel):
    """Authentication token response schema."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: Optional[int] = Field(None, description="Token expiration in seconds")
    refresh_token: Optional[str] = Field(None, description="Refresh token")
    scope: Optional[str] = Field("", description="Token scope")


class TokenPayload(BaseModel):
    """JWT token payload schema."""
    sub: Optional[str] = Field(None, description="Subject (user ID)")
    exp: Optional[datetime] = Field(None, description="Expiration time")
    iat: Optional[datetime] = Field(None, description="Issued at")
    jti: Optional[str] = Field(None, description="JWT ID")
    scopes: list[str] = Field(default_factory=list, description="Token scopes")
    type: Optional[str] = Field("access", description="Token type (access or refresh)")
    
    # Custom claims
    username: Optional[str] = Field(None, description="Username")
    email: Optional[str] = Field(None, description="User email")
    is_active: bool = Field(True, description="User active status")
    is_superuser: bool = Field(False, description="Superuser status")
    permissions: list[str] = Field(default_factory=list, description="User permissions")


class TokenData(BaseModel):
    """Token data schema for login."""
    username: Optional[str] = None
    scopes: list[str] = []


class OAuth2TokenRequestForm(BaseModel):
    """OAuth2 token request form."""
    grant_type: str = Field(..., description="Grant type")
    username: Optional[str] = Field(None, description="Username")
    password: Optional[str] = Field(None, description="Password")
    scope: str = Field("", description="Token scope")
    client_id: Optional[str] = Field(None, description="Client ID")
    client_secret: Optional[str] = Field(None, description="Client secret")
    refresh_token: Optional[str] = Field(None, description="Refresh token")
