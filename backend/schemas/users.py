"""Request and response schemas for user accounts."""

import re

from pydantic import BaseModel, Field, field_validator


class UserCreate(BaseModel):
    email: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not re.fullmatch(r"[^@\s]+@unomaha\.edu", normalized):
            raise ValueError("Use your @unomaha.edu email address.")
        return normalized

    @field_validator("first_name", "last_name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = " ".join(value.strip().split())
        if not normalized:
            raise ValueError("This field is required.")
        return normalized


class UserLogin(BaseModel):
    email: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not re.fullmatch(r"[^@\s]+@unomaha\.edu", normalized):
            raise ValueError("Use your @unomaha.edu email address.")
        return normalized

class UserCreated(BaseModel):
    email: str


class UserLoggedIn(UserCreated):
    first_name: str
    last_name: str


class UserProfile(BaseModel):
    email: str
    first_name: str
    last_name: str
