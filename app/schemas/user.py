"""User related schemas."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.base import IDSchemaMixin, TimestampMixin


# Shared properties
class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: Optional[EmailStr] = Field(
        None, 
        description="Email address (must be unique)",
        example="user@example.com"
    )
    is_active: bool = Field(
        True, 
        description="Whether the user is active"
    )
    is_superuser: bool = Field(
        False, 
        description="Whether the user has superuser privileges"
    )
    full_name: Optional[str] = Field(
        None, 
        description="User's full name",
        example="John Doe"
    )
    
    @field_validator("email")
    @classmethod
    def email_must_be_lowercase(cls, v: Optional[str]) -> Optional[str]:
        """Ensure email is lowercase."""
        if v is None:
            return v
        return v.lower()


# Properties to receive via API on creation
class UserCreate(UserBase):
    """Schema for creating a new user."""
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=8, max_length=100, description="Password")


# Properties to receive via API on update
class UserUpdate(UserBase):
    """Schema for updating an existing user."""
    password: Optional[str] = Field(
        None, 
        min_length=8, 
        max_length=100, 
        description="New password (if updating)"
    )


# Properties shared by models stored in DB
class UserInDBBase(IDSchemaMixin, TimestampMixin, UserBase):
    """Base schema for user data stored in the database."""
    email: Optional[EmailStr] = Field(None, description="Email address")
    hashed_password: str = Field(..., description="Hashed password")
    last_login: Optional[datetime] = Field(
        None, 
        description="Last login timestamp"
    )
    is_verified: bool = Field(
        False, 
        description="Whether the user has verified their email"
    )

    class Config:
        from_attributes = True


# Properties to return to client
class User(IDSchemaMixin, TimestampMixin, UserBase):
    """User schema for API responses."""
    id: int = Field(..., description="User ID")
    is_verified: bool = Field(..., description="Email verification status")
    last_login: Optional[datetime] = Field(
        None, 
        description="Last login timestamp"
    )


# Properties stored in DB
class UserInDB(UserInDBBase):
    """User schema for database operations."""
    pass


# Additional properties to return via API
class UserWithToken(User):
    """User schema with authentication token."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")


# Additional properties stored in DB
class UserInDBWithPassword(UserInDB):
    """User schema with password for internal use."""
    pass


# Request/Response models for password reset
class PasswordResetRequest(BaseModel):
    """Schema for requesting a password reset."""
    email: EmailStr = Field(..., description="User's email address")


class PasswordResetConfirm(BaseModel):
    """Schema for confirming a password reset."""
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password")


# Request/Response models for email verification
class EmailVerificationRequest(BaseModel):
    """Schema for requesting an email verification."""
    email: EmailStr = Field(..., description="User's email address to verify")


class EmailVerificationConfirm(BaseModel):
    """Schema for confirming an email verification."""
    token: str = Field(..., description="Email verification token")


# Request/Response models for user permissions
class UserPermissionUpdate(BaseModel):
    """Schema for updating user permissions."""
    permissions: List[str] = Field(
        ..., 
        description="List of permission strings"
    )


# Response models for user operations
class UserResponse(BaseModel):
    """Generic user operation response."""
    success: bool = Field(..., description="Operation status")
    message: str = Field(..., description="Result message")
    user: Optional[User] = Field(None, description="User details")


class UsersResponse(BaseModel):
    """Response for listing multiple users."""
    success: bool = Field(..., description="Operation status")
    count: int = Field(..., description="Number of users")
    users: List[User] = Field(..., description="List of users")
