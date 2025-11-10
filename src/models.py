from pydantic import BaseModel
from pydantic import validator
from datetime import date, time
from typing import Optional

class Event(BaseModel):
    name: str
    date: date
    start_time: time
    end_time: time
    category: Optional[str] = None

#validation method to make sure start time and end time are valid. this checks for a case where the start time is greater than the end time which should not be possible
    @validator("end_time")
    def check_time_order(cls, end_time, values):
        start_time = values.get("start_time")
        if start_time is not None and end_time <= start_time:
            raise ValueError("End time must be after start time")
        return end_time
    

class Task(BaseModel):
    title: str
    course: Optional[str] = None
    estimated_minutes: int
    priority: int
    due_date: date
    notes: Optional[str] = None

    @validator("estimated_minutes")
    def check_estimated_minutes(cls, estimated_minutes):
        if estimated_minutes <= 0:
            raise ValueError("Estimated minutes must be greater than 0")
        return estimated_minutes
    
    @validator("priority")
    def check_priority(cls, priority):
        if priority < 1 or priority > 5:
            raise ValueError("Priority must be between 1 and 5")
        return priority
    
    @validator("due_date")
    def check_due_date(cls, due_date):
        if due_date < date.today():
            raise ValueError("Due date cannot be in the past")
        return due_date
    
class WellnessGoal(BaseModel):
    min_sleep_hours_per_day: float
    workouts_per_week: int
    meals_per_day: int
    self_care_blocks_per_week: int

    @validator("min_sleep_hours_per_day")
    def check_sleep_hours(cls, min_sleep_hours_per_day):
        if min_sleep_hours_per_day <= 0:
            raise ValueError("sleep hours must be greater than 0")
        return min_sleep_hours_per_day
    
    @validator("workouts_per_week")
    def check_workouts(cls, workouts_per_week):
        if workouts_per_week < 0:
            raise ValueError("Workouts per week cannot be negative")
        return workouts_per_week
    
    @validator("meals_per_day")
    def check_meals(cls, meals_per_day):
        if meals_per_day < 1:
            raise ValueError("Meals per day must be at least 1")
        return meals_per_day
    
    @validator("self_care_blocks_per_week")
    def check_self_care(cls, self_care_blocks_per_week):
        if self_care_blocks_per_week < 0:
            raise ValueError("self-care blocks per week cannot be negative")
        return self_care_blocks_per_week