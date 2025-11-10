from datetime import date, time
from src.models import Event, Task

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