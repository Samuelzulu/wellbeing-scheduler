from datetime import date, time
from typing import Optional, List, Dict
from pydantic import BaseModel, field_validator, ConfigDict


# Task schemas
class TaskCreate(BaseModel):
    title: str
    course: Optional[str] = None
    estimated_minutes: int
    priority: int
    due_date: date
    notes: Optional[str] = None

    @field_validator("estimated_minutes")
    @classmethod
    def check_estimated_minutes(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("estimated_minutes must be greater than 0")
        return v

    @field_validator("priority")
    @classmethod
    def check_priority(cls, v: int) -> int:
        if v < 1 or v > 5:
            raise ValueError("priority must be between 1 and 5")
        return v

    @field_validator("due_date")
    @classmethod
    def check_due_date(cls, v: date) -> date:
        if v < date.today():
            raise ValueError("due_date cannot be in the past")
        return v


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    course: Optional[str] = None
    estimated_minutes: Optional[int] = None
    priority: Optional[int] = None
    due_date: Optional[date] = None
    notes: Optional[str] = None


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    course: Optional[str]
    estimated_minutes: int
    priority: int
    due_date: date
    notes: Optional[str]


# Event schemas
class EventCreate(BaseModel):
    name: str
    date: date
    start_time: time
    end_time: time
    category: Optional[str] = None

    @field_validator("end_time", mode="after")
    @classmethod
    def check_time_order(cls, end_time: time, info) -> time:
        start_time = info.data.get("start_time")
        if start_time is not None and end_time <= start_time:
            raise ValueError("end_time must be after start_time")
        return end_time


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    date: date
    start_time: time
    end_time: time
    category: Optional[str]


# Plan schemas
class PlanRequest(BaseModel):
    """All fields are optional — defaults match the CLI defaults."""
    sleep: float = 7.0
    workouts: int = 3
    meals: int = 3
    self_care: int = 2
    earliest: str = "08:00"
    latest: str = "22:00"
    block_minutes: int = 60
    break_minutes: int = 15

    @field_validator("sleep")
    @classmethod
    def check_sleep(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("sleep must be greater than 0")
        return v

    @field_validator("workouts", "meals", "self_care")
    @classmethod
    def check_non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("value must be non-negative")
        return v

    @field_validator("block_minutes")
    @classmethod
    def check_block(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("block_minutes must be greater than 0")
        return v

    @field_validator("break_minutes")
    @classmethod
    def check_break(cls, v: int) -> int:
        if v < 0:
            raise ValueError("break_minutes cannot be negative")
        return v


class PlanBlockResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    day: date
    start_time: time
    end_time: time
    category: str


class PlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: date
    week_start: date
    weekly_balance_score: Optional[float]
    blocks: List[PlanBlockResponse]


class PlanSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: date
    week_start: date
    weekly_balance_score: Optional[float]