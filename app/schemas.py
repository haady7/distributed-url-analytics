from datetime import datetime, timezone
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl, StringConstraints, field_validator

Code = Annotated[str, StringConstraints(min_length=3, max_length=32, pattern=r"^[A-Za-z0-9_-]+$")]


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    created_at: datetime


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class URLCreate(BaseModel):
    original_url: HttpUrl = Field(max_length=2048)
    custom_code: Code | None = None
    expires_at: datetime | None = None

    @field_validator("expires_at")
    @classmethod
    def expiry_must_be_future(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return value
        now = datetime.now(timezone.utc)
        comparable = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        if comparable <= now:
            raise ValueError("expires_at must be in the future")
        return comparable


class URLRead(BaseModel):
    code: str
    original_url: str
    short_url: str
    created_at: datetime
    expires_at: datetime | None
    is_active: bool


class DailyClicks(BaseModel):
    date: str
    clicks: int


class CountryClicks(BaseModel):
    country: str
    clicks: int


class URLAnalytics(BaseModel):
    code: str
    total_clicks: int
    daily_clicks: list[DailyClicks]
    top_countries: list[CountryClicks]
    top_referrers: list[dict[str, str | int]]
