from datetime import datetime, time, timedelta, date
from typing import List
from .models import Event, Task, WellnessGoal, Preferences

def generate_weekly_plan (
        events: List[Event],
        tasks: List[Task],
        goals: WellnessGoal,
        prefs: Preferences
):
    """
    Generate a weeklyy schedule plan on user input.
    Steps (to be implemented):
        1. Create weekly time grid
        2. Place sleep blocks
        3. Place fixed events
        4. Identify open slots
        5. (Later) Insert meals, study, workouts
    """
    today = date.today()

    #how many days until next Monday
    days_until_monday = (7 - today.weekday()) % 7
    monday = today + timedelta(days = days_until_monday)

    #build list of 7 dates starting monday
    week_dates = [monday + timedelta(days = i) for i in range(7)]

    #dictionary form
    weekly_grid = {d: [] for d in week_dates}

    sleep_duration = timedelta(hours = goals.min_sleep_hours_per_day)

    for day in weekly_grid:
        sleep_start_dt = datetime.combine(day, prefs.latest_end)
        sleep_end_dt = sleep_start_dt + sleep_duration

        sleep_block = {
            "start": sleep_start_dt.time(),
            "end": sleep_end_dt.time(),
            "category": "sleep"
        }

        weekly_grid[day].append(sleep_block)

    print(weekly_grid)
    return weekly_grid

if __name__ == "__main__":
    #temporary manual test
    from .models import Event, Task, WellnessGoal, Preferences
    from datetime import time, date
    #dummy test objects
    e = []
    t = []
    g = WellnessGoal(min_sleep_hours_per_day = 7, workouts_per_week = 3, meals_per_day = 3, self_care_blocks_per_week = 2)
    p = Preferences(earliest_start = time(8, 0), latest_end = time(22, 0), study_block_minutes = 60, break_minutes = 15)

    generate_weekly_plan(e, t, g, p)