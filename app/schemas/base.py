# File: app/schemas/base.py
# Purpose: Shared base schemas used by tests

from pydantic import BaseModel, EmailStr, Field, ConfigDict, model_validator


class UserBase(BaseModel):
    first_name: str = Field(max_length=50, example="John")
    last_name: str = Field(max_length=50, example="Doe")
    email: EmailStr = Field(example="john.doe@example.com")
    username: str = Field(min_length=3, max_length=50, example="johndoe")

    model_config = ConfigDict(from_attributes=True)


class PasswordMixin(BaseModel):
    password: str = Field(..., min_length=8, example="SecurePass123")

    @model_validator(mode="after")
    def validate_password(self) -> "PasswordMixin":
        pw = self.password
        if not any(c.isupper() for c in pw):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in pw):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in pw):
            raise ValueError("Password must contain at least one digit")
        return self

    model_config = ConfigDict(from_attributes=True)


class UserCreate(UserBase, PasswordMixin):
    """Schema for creating a new user (tests use this)."""
    pass


class UserLogin(BaseModel):
    username: str = Field(min_length=3, max_length=50, example="johndoe")
    password: str = Field(min_length=8, example="SecurePass123")
