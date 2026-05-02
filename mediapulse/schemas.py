from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field


def calculate_age(birth_date: date) -> int:
    today = date.today()
    years = today.year - birth_date.year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        years -= 1
    return max(years, 0)


def get_age_group(age: int) -> str:
    if age < 18:
        return "under_18"
    if age < 25:
        return "18-24"
    if age < 35:
        return "25-34"
    if age < 45:
        return "35-44"
    if age < 55:
        return "45-54"
    return "55+"


class UserCreate(BaseModel):
    first_name: str
    last_name: str
    birth_date: date
    occupation: str
    sex: str
    region: str
    phone_number: Optional[str] = None
    email: Optional[str] = None
    consent_microphone: bool = False
    consent_location: bool = False
    consent_rewards: bool = False
    consent_demographic_analytics: bool = False


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    birth_date: Optional[date] = None
    occupation: Optional[str] = None
    sex: Optional[str] = None
    region: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    consent_microphone: Optional[bool] = None
    consent_location: Optional[bool] = None
    consent_rewards: Optional[bool] = None
    consent_demographic_analytics: Optional[bool] = None


class UserResponse(BaseModel):
    id: int
    first_name: str
    last_name: str
    birth_date: date
    age: int
    age_group: str
    occupation: str
    sex: str
    region: str
    phone_number: Optional[str]
    email: Optional[str]
    points: int
    consent_microphone: bool
    consent_location: bool
    consent_rewards: bool
    consent_demographic_analytics: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ChannelCreate(BaseModel):
    name: str
    media_type: str
    source_type: str
    source_url: str
    active: bool = True


class ChannelUpdate(BaseModel):
    name: Optional[str] = None
    media_type: Optional[str] = None
    source_type: Optional[str] = None
    source_url: Optional[str] = None
    active: Optional[bool] = None


class ChannelResponse(BaseModel):
    id: int
    name: str
    media_type: str
    source_type: str
    source_url: str
    active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class MediaDetectionResponse(BaseModel):
    detected: bool
    media_type: Optional[str]
    channel: Optional[str]
    confidence: float
    matched_time: Optional[str]
    points_earned: int
    message: Optional[str] = None


class DetectHashesRequest(BaseModel):
    user_id: int
    timestamp: str
    hashes: List[list]  # Will be List of [hash_string, time_float]


class OOHEventCreate(BaseModel):
    user_id: int
    panel_id: str
    timestamp: datetime
    distance_meters: float


class OOHEventResponse(BaseModel):
    saved: bool
    message: str
    points_earned: int


class RewardResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    points_cost: int
    sponsor_name: Optional[str]
    supermarket_name: Optional[str]
    discount_type: Optional[str]
    discount_value: Optional[str]
    valid_until: Optional[date]

    class Config:
        from_attributes = True


class RewardRedeemRequest(BaseModel):
    user_id: int
    reward_id: int


class LiveStatusItem(BaseModel):
    channel_id: int
    name: str
    media_type: str
    source_type: str
    source_url: str
    active: bool
    worker_running: bool
    recent_fingerprints: int
    last_chunk_time: Optional[str]
    last_error: Optional[str]


class LiveStatusResponse(BaseModel):
    redis_connected: bool
    channels: List[LiveStatusItem] = Field(default_factory=list)
