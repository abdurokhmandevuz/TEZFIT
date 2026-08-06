from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import BigInteger, Integer, Float, String, Boolean, DateTime, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.base import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    weight_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True, default=70.0)
    height_cm: Mapped[Optional[float]] = mapped_column(Float, nullable=True, default=170.0)
    age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=25)
    gender: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default="male")  # male / female
    
    daily_goal_kcal: Mapped[float] = mapped_column(Float, default=2000.0)
    is_vip: Mapped[bool] = mapped_column(Boolean, default=False)
    streak_days: Mapped[int] = mapped_column(Integer, default=0)
    free_requests_today: Mapped[int] = mapped_column(Integer, default=0)
    last_request_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    last_streak_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    meals: Mapped[List["Meal"]] = relationship("Meal", back_populates="user", cascade="all, delete-orphan")
    achievements: Mapped[List["Achievement"]] = relationship("Achievement", back_populates="user", cascade="all, delete-orphan")
    reminders: Mapped[List["Reminder"]] = relationship("Reminder", back_populates="user", cascade="all, delete-orphan")

class Meal(Base):
    __tablename__ = "meals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    photo_file_id: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    food_name: Mapped[str] = mapped_column(String(255), nullable=False)
    weight_g: Mapped[float] = mapped_column(Float, default=0.0)
    calories: Mapped[float] = mapped_column(Float, default=0.0)
    protein_g: Mapped[float] = mapped_column(Float, default=0.0)
    fat_g: Mapped[float] = mapped_column(Float, default=0.0)
    carbs_g: Mapped[float] = mapped_column(Float, default=0.0)
    meal_time: Mapped[str] = mapped_column(String(50), default="snack")  # breakfast, lunch, dinner, snack
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="meals")

class Achievement(Base):
    __tablename__ = "achievements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    badge_code: Mapped[str] = mapped_column(String(100), nullable=False)
    earned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="achievements")

class Reminder(Base):
    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reminder_time: Mapped[str] = mapped_column(String(10), nullable=False, default="08:00")
    reminder_type: Mapped[str] = mapped_column(String(50), nullable=False, default="breakfast")  # breakfast, lunch, dinner
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    user: Mapped["User"] = relationship("User", back_populates="reminders")
