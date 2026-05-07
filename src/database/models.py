from datetime import date, time
from sqlalchemy import (
    Column, Integer, String, Float, Boolean,
    Date, Time, ForeignKey, Text
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass

class UserORM(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    created_at = Column(Date, nullable=False)
    plans = relationship("PlanORM", back_populates="user", cascade="all, delete-orphan")
    tasks = relationship("TaskORM", back_populates="user", cascade="all, delete-orphan")
    events = relationship("EventORM", back_populates="user", cascade="all, delete-orphan")
    
class TaskORM(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    course = Column(String, nullable=True)
    estimated_minutes = Column(Integer, nullable=False)
    priority = Column(Integer, nullable=False)
    due_date = Column(Date, nullable=False)
    notes = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user = relationship("UserORM", back_populates="tasks")


class EventORM(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    category = Column(String, nullable=True)
    category = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user = relationship("UserORM", back_populates="events")


class WellnessGoalORM(Base):
    __tablename__ = "wellness_goals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    min_sleep_hours_per_day = Column(Float, nullable=False)
    workouts_per_week = Column(Integer, nullable=False)
    meals_per_day = Column(Integer, nullable=False)
    self_care_blocks_per_week = Column(Integer, nullable=False)


class PreferencesORM(Base):
    __tablename__ = "preferences"

    id = Column(Integer, primary_key=True, autoincrement=True)
    earliest_start = Column(Time, nullable=False)
    latest_end = Column(Time, nullable=False)
    study_block_minutes = Column(Integer, nullable=False)
    break_minutes = Column(Integer, nullable=False)


class PlanORM(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(Date, nullable=False)
    week_start = Column(Date, nullable=False)
    weekly_balance_score = Column(Float, nullable=True)
    weekly_balance_score = Column(Float, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    share_token = Column(String, unique=True, nullable=True, index=True)
    user = relationship("UserORM", back_populates="plans")
    blocks = relationship("PlanBlockORM", back_populates="plan", cascade="all, delete-orphan")
    blocks = relationship("PlanBlockORM", back_populates="plan", cascade="all, delete-orphan")


class PlanBlockORM(Base):
    __tablename__ = "plan_blocks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)
    day = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    category = Column(String, nullable=False)
    plan = relationship("PlanORM", back_populates="blocks")