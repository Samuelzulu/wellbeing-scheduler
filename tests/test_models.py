from datetime import date, time
from src.models import Event, Task, WellnessGoal, Preferences

e = Event (
    name = "COMP 232 Lecture",
    date = date(2025, 3, 10),
    start_time = time(9, 0),
    end_time = time(10, 0)
)

print(e)

t = Task (
    title = "Study for COMP 232 Quiz",
    estimated_minutes = 90,
    priority = 3,
    due_date = date(2025, 12, 15)
)

print(t)

w = WellnessGoal (
    min_sleep_hours_per_day = 7.5,
    workouts_per_week = 3,
    meals_per_day = 3,
    self_care_blocks_per_week = 2
)

print(w)

p = Preferences (
    earliest_start = time(8, 0),
    latest_end = time(22, 0),
    study_block_minutes = 60,
    break_minutes = 15
)

print(p)
