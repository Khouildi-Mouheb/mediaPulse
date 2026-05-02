from datetime import datetime

from sqlalchemy import Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, String

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    birth_date = Column(Date, nullable=False)
    occupation = Column(String, nullable=False)
    sex = Column(String, nullable=False)
    region = Column(String, nullable=False)
    phone_number = Column(String, nullable=True)
    email = Column(String, nullable=True)
    consent_microphone = Column(Boolean, default=False)
    consent_location = Column(Boolean, default=False)
    consent_rewards = Column(Boolean, default=False)
    consent_demographic_analytics = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Channel(Base):
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    media_type = Column(String, nullable=False)
    source_type = Column(String, nullable=False)
    source_url = Column(String, nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class MediaDetection(Base):
    __tablename__ = "media_detections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=True)
    media_type = Column(String, nullable=True)
    confidence = Column(Float, default=0.0)
    detected = Column(Boolean, default=False)
    detected_at = Column(DateTime, default=datetime.utcnow)
    matched_time = Column(DateTime, nullable=True)


class Billboard(Base):
    __tablename__ = "billboards"

    id = Column(Integer, primary_key=True, index=True)
    panel_id = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    region = Column(String, nullable=False)
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    radius_meters = Column(Integer, default=50)
    visibility_score = Column(Float, default=1.0)


class OOHEvent(Base):
    __tablename__ = "ooh_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    billboard_id = Column(Integer, ForeignKey("billboards.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    distance_meters = Column(Float, nullable=False)


class UserPoints(Base):
    __tablename__ = "user_points"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    total_points = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PointsTransaction(Base):
    __tablename__ = "points_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    type = Column(String, nullable=False)
    description = Column(String, nullable=False)
    points = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)


class Reward(Base):
    __tablename__ = "rewards"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    points_cost = Column(Integer, nullable=False)
    sponsor_name = Column(String, nullable=True)
    supermarket_name = Column(String, nullable=True)
    discount_type = Column(String, nullable=True)
    discount_value = Column(String, nullable=True)
    valid_until = Column(Date, nullable=True)
    active = Column(Boolean, default=True)


class RewardRedemption(Base):
    __tablename__ = "reward_redemptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reward_id = Column(Integer, ForeignKey("rewards.id"), nullable=False)
    coupon_code = Column(String, nullable=False)
    redeemed_at = Column(DateTime, default=datetime.utcnow)
    points_spent = Column(Integer, nullable=False)
