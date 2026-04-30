from pydantic import BaseModel, ConfigDict, field_validator
from datetime import date, time
from typing import Optional


class Event(BaseModel):
    name: str
    date: date
    start_time: time
    end_time: time
    category: Optional[str] = None

    # validation: end_time must be after start_time
    @field_validator("end_time", mode="after")
    @classmethod
    def check_time_order(cls, end_time, info):
        start_time = info.data.get("start_time")
        if start_time is not None and end_time <= start_time:
            raise ValueError("End time must be after start time")
        return end_time


class Task(BaseModel):
    model_config = ConfigDict(frozen=False)  # engine mutates estimated_minutes

    title: str
    course: Optional[str] = None
    estimated_minutes: int
    priority: int
    due_date: date
    notes: Optional[str] = None

    @field_validator("estimated_minutes")
    @classmethod
    def check_estimated_minutes(cls, v):
        if v <= 0:
            raise ValueError("Estimated minutes must be greater than 0")
        return v

    @field_validator("priority")
    @classmethod
    def check_priority(cls, v):
        if v < 1 or v > 5:
            raise ValueError("Priority must be between 1 and 5")
        return v

    @field_validator("due_date")
    @classmethod
    def check_due_date(cls, v):
        if v < date.today():
            raise ValueError("Due date cannot be in the past")
        return v


class WellnessGoal(BaseModel):
    min_sleep_hours_per_day: float
    workouts_per_week: int
    meals_per_day: int
    self_care_blocks_per_week: int

    @field_validator("min_sleep_hours_per_day")
    @classmethod
    def check_sleep_hours(cls, v):
        if v <= 0:
            raise ValueError("Sleep hours must be greater than 0")
        return v

    @field_validator("workouts_per_week")
    @classmethod
    def check_workouts(cls, v):
        if v < 0:
            raise ValueError("Workouts per week cannot be negative")
        return v

    @field_validator("meals_per_day")
    @classmethod
    def check_meals(cls, v):
        if v < 1:
            raise ValueError("Meals per day must be at least 1")
        return v

    @field_validator("self_care_blocks_per_week")
    @classmethod
    def check_self_care(cls, v):
        if v < 0:
            raise ValueError("Self-care blocks per week cannot be negative")
        return v


class Preferences(BaseModel):
    earliest_start: time
    latest_end: time
    study_block_minutes: int
    break_minutes: int

    @field_validator("latest_end", mode="after")
    @classmethod
    def check_time_order(cls, latest_end, info):
        earliest_start = info.data.get("earliest_start")
        if earliest_start and latest_end <= earliest_start:
            raise ValueError("latest_end must be after earliest_start")
        return latest_end

    @field_validator("study_block_minutes")
    @classmethod
    def check_study_block_minutes(cls, v):
        if v <= 0:
            raise ValueError("Study block minutes must be greater than 0")
        return v

    @field_validator("break_minutes")
    @classmethod
    def check_break_minutes(cls, v):
        if v < 0:
            raise ValueError("Break minutes cannot be negative")
        return v