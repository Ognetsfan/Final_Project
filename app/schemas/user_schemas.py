from builtins import ValueError, any, bool, str
from pydantic import BaseModel, EmailStr, HttpUrl, Field, validator, root_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum
import uuid
import re
from app.models.user_model import UserRole
from app.utils.nickname_gen import generate_nickname

# Helper function to validate URLs
def validate_url(url: Optional[str]) -> Optional[str]:
    if url is None:
        return url
    url_regex = r'^https?:\/\/[^\s/$.?#].[^\s]*$'
    if not re.match(url_regex, url):
        raise ValueError('Invalid URL format')
    return url

# Base schema for shared user fields
class UserBase(BaseModel):
    email: EmailStr = Field(..., example="john.doe@example.com")
    nickname: Optional[str] = Field(None, min_length=3, pattern=r'^[\w-]+$', example=generate_nickname())
    first_name: Optional[str] = Field(None, example="John")
    last_name: Optional[str] = Field(None, example="Doe")
    bio: Optional[str] = Field(None, example="Experienced software developer specializing in web applications.")
    profile_picture_url: Optional[str] = Field(None, example="https://example.com/profiles/john.jpg")
    linkedin_profile_url: Optional[str] = Field(None, example="https://linkedin.com/in/johndoe")
    github_profile_url: Optional[str] = Field(None, example="https://github.com/johndoe")
    role: UserRole

    _validate_urls = validator('profile_picture_url', 'linkedin_profile_url', 'github_profile_url', pre=True, allow_reuse=True)(validate_url)

    class Config:
        from_attributes = True

# Schema for creating a user
class UserCreate(UserBase):
    password: str = Field(..., example="Secure*1234")

# Schema for updating a user
class UserUpdate(UserBase):
    email: Optional[EmailStr] = Field(None, example="john.doe@example.com")
    nickname: Optional[str] = Field(None, min_length=3, pattern=r'^[\w-]+$', example="john_doe123")
    first_name: Optional[str] = Field(None, example="John")
    last_name: Optional[str] = Field(None, example="Doe")
    bio: Optional[str] = Field(None, example="Experienced software developer specializing in web applications.")
    profile_picture_url: Optional[str] = Field(None, example="https://example.com/profiles/john.jpg")
    linkedin_profile_url: Optional[str] = Field(None, example="https://linkedin.com/in/johndoe")
    github_profile_url: Optional[str] = Field(None, example="https://github.com/johndoe")
    role: Optional[str] = Field(None, example="AUTHENTICATED")

    @root_validator(pre=True)
    def check_at_least_one_value(cls, values):
        if not any(values.values()):
            raise ValueError("At least one field must be provided for update")
        return values

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None # Email
    name: Optional[str] = Field(None, max_length=50)
    bio: Optional[str] = Field(None, max_length=255)
    location: Optional[str] = Field(None, max_length=100)
    password: Optional[str] = Field(None, min_length=8)
    linkedin_profile_url: Optional[HttpUrl] = None 
    github_profile_url: Optional[HttpUrl] = None 

    @validator("name", "bio", "location", pre=True, always=True)
    def strip_whitespace(cls, v):
        return v.strip() if isinstance(v, str) else v

    class Config:
        orm_mode = True

    def dict(self, *args, **kwargs):
        """
        Override to convert HttpUrl fields to strings when exporting to dict.
        """
        data = super().dict(*args, **kwargs)
        if "linkedin_profile_url" in data and data["linkedin_profile_url"]:
            data["linkedin_profile_url"] = str(data["linkedin_profile_url"])
        if "github_profile_url" in data and data["github_profile_url"]:
            data["github_profile_url"] = str(data["github_profile_url"])
        return data
# Schema for responding with user data
class UserResponse(UserBase):
    id: uuid.UUID = Field(..., example=uuid.uuid4())
    is_professional: Optional[bool] = Field(default=False, example=True)
    created_at: datetime = Field(..., example="2023-01-01T12:00:00Z")
    updated_at: datetime = Field(..., example="2023-01-02T12:00:00Z")

# Schema for login request
class LoginRequest(BaseModel):
    email: str = Field(..., example="john.doe@example.com")
    password: str = Field(..., example="Secure*1234")

# Schema for error response
class ErrorResponse(BaseModel):
    error: str = Field(..., example="Not Found")
    details: Optional[str] = Field(None, example="The requested resource was not found.")

# Schema for paginated list of users
class UserListResponse(BaseModel):
    items: List[UserResponse] = Field(..., example=[{
        "id": uuid.uuid4(), "nickname": generate_nickname(), "email": "john.doe@example.com",
        "first_name": "John", "bio": "Experienced developer", "role": "AUTHENTICATED",
        "last_name": "Doe", "bio": "Experienced developer", "role": "AUTHENTICATED",
        "profile_picture_url": "https://example.com/profiles/john.jpg", 
        "linkedin_profile_url": "https://linkedin.com/in/johndoe", 
        "github_profile_url": "https://github.com/johndoe"
    }])
    total: int = Field(..., example=100)
    page: int = Field(..., example=1)
    size: int = Field(..., example=10)
