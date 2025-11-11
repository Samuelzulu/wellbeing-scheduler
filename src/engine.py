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

    #place fixed events (classes, appointments, shifts, etc.)
    for event in events:
        event_day = event.date
        if event_day not in weekly_grid:
            continue    #skip over days that are outside 7-day range

        #build datetime versions of event start/end
        event_start_dt = datetime.combine(event_day, event.start_time)
        event_end_dt = datetime.combine(event_day, event.end_time)

        #checking for overlaps
        overlap = False
        for block in weekly_grid[event_day]:
            block_start = datetime.combine(event_day, block["start"])
            block_end = datetime.combine(event_day, block["end"])
            #if the event overlaps with any block flag it
            if not (event_end_dt <= block_start or event_start_dt >= block_end):
                overlap = True
                print(f"Overlap detected on {event_day} with {block['category']}")
                break

        #add event only if no overlap
        if not overlap:
            event_block = {
                "start": event.start_time,
                "end": event.end_time,
                "category": event.category or "event"
            }
            weekly_grid[event_day].append(event_block)
            
      #sort blocks for each day
    for day, blocks in weekly_grid.items():
        weekly_grid[day] = sorted(blocks, key = lambda b: b["start"])
            
    print_schedule(weekly_grid)
    return weekly_grid

def print_schedule(weekly_grid):
    print("\n====================== WEEKLY SCHEDULE ======================\n")
    for day, blocks in weekly_grid.items():
        print(f"{day.strftime('%A, %B %d, %Y')}")
        if not blocks:
            print(" (No scheduled activities)")
        for block in blocks:
            start = block['start'].strftime("%H:%M")
            end = block['end'].strftime("%H:%M")
            category = block['category'].capitalize()
            print(f" {category}: {start} -> {end}")
        print() #blank line between days
        
if __name__ == "__main__":
    from .models import Event, Task, WellnessGoal, Preferences
    from datetime import time, date
    
    events = [
        Event(
            name = "Comp 232 Lecture",
            date = date(2025, 11, 17),
            start_time = time(9, 0),
            end_time = time(10, 0),
            category = "study"
        ),
    ]
    
    tasks = []
    goals = WellnessGoal(min_sleep_hours_per_day = 7, workouts_per_week = 3, meals_per_day = 3, self_care_blocks_per_week = 2)
    prefs = Preferences(earliest_start = time(8, 0), latest_end = time(22, 0), study_block_minutes = 60, break_minutes = 15)
    
    generate_weekly_plan(events, tasks, goals, prefs)