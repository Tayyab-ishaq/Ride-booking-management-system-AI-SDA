from __future__ import annotations

from typing import Annotated
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator, field_validator

from core.enums import UserRole


class RegisterRequest(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=60)
    last_name: str | None = Field(default=None, max_length=60)
    full_name: str | None = Field(default=None, min_length=1, max_length=120)
    email: EmailStr
    password: Annotated[str, Field(min_length=6, max_length=128)]
    confirm_password: Annotated[str, Field(min_length=6, max_length=128)]
    
    @field_validator('password')
    def password_min_length(cls, v: str):
        if len(v or "") < 6:
            raise ValueError("Password must be at least 6 characters")
        return v

    @field_validator('confirm_password')
    def confirm_password_min_length(cls, v: str):
        if len(v or "") < 6:
            raise ValueError("Confirm password must be at least 6 characters")
        return v
    role: UserRole = UserRole.rider

    @model_validator(mode="after")
    def validate_password_confirmation(self) -> RegisterRequest:
        if self.password != self.confirm_password:
            raise ValueError("Password and confirm_password must match")
        if self.full_name is None:
            if not self.first_name:
                raise ValueError("first_name must be provided")
            parts = [self.first_name.strip()]
            if self.last_name:
                parts.append(self.last_name.strip())
            self.full_name = " ".join(part for part in parts if part).strip()
        return self


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str
    email: EmailStr
    role: UserRole
    created_at: datetime
    updated_at: datetime