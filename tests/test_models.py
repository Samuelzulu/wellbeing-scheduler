from datetime import date, time
from src.models import Event

e = Event (
    name = "COMP 232 Lecture",
    date = date(2025, 3, 10),
    start_time = time(9, 0),
    end_time = time(10, 0)
)

print(e)