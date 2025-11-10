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