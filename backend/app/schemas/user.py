from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128, description="User password (minimum 6 characters)")


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, description="User password")


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
