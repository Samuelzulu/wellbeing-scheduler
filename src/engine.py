from datetime import datetime, time, timedelta, date
from typing import List
from .models import Event, Task, WellnessGoal, Preferences

def find_open_slots_for_day(day, blocks, prefs):
    """
    Return list of (start_time, end_time) tuples representing free gaps within the day window
    [prefs.earliest_start, prefs.latest_end], excluding existing blocks.
    Overnight blocks (end <= start) are ignored for the daytime window in V1.
    """
    window_start = datetime.combine(day, prefs.earliest_start)
    window_end = datetime.combine(day, prefs.latest_end)
    
    # collect occupied intervals within the window (clamped)
    occupied = []
    for b in blocks:
        start_dt = datetime.combine(day, b["start"])
        end_dt = datetime.combine(day, b["end"])
        
        # skip overnight (end <= start) for daytime window in V1
        if end_dt <= start_dt:
            continue
        
        # completely outside window
        if end_dt <= window_start or start_dt >= window_end:
            continue
        
        # clamp to window
        start_dt = max(start_dt, window_start)
        end_dt = min(end_dt, window_end)
        occupied.append((start_dt, end_dt))
        
    # sort and merge occupied intervals
    occupied.sort(key = lambda x: x[0])
    merged = []
    for interval in occupied:
        if not merged or interval[0] > merged[-1][1]:
            merged.append(list((interval)))
        else:
            merged[-1][1] = max(merged[-1][1], interval[1])
            
    # ind gaps between merged occupied intervals
    gaps = []
    cur = window_start
    min_gap = timedelta(minutes = prefs.study_block_minutes)    # minimum useful gap
    
    for start, end in merged:
        if start - cur >= min_gap:
            gaps.append((cur.time(), start.time()))
        cur = max(cur, end)
        
    # tail gap
    if window_end - cur >= min_gap:
        gaps.append((cur.time(), window_end.time()))
        
    return gaps
        
def sort_tasks_for_scheduling (tasks):
    # priority: higher first, due_date: earlier first
    return sorted(tasks, key=lambda t: (-t.priority, t.due_date))

def place_study_for_day (day, weekly_grid, tasks, prefs):
    gaps = find_open_slots_for_day(day, weekly_grid[day], prefs)
    
    block_len = timedelta(minutes=prefs.study_block_minutes)
    
    for gap_start_t, gap_end_t in gaps:
        gap_start = datetime.combine(day, gap_start_t)
        gap_end = datetime.combine(day, gap_end_t)
        
        cursor = gap_start
        
        # keep placing blocks while there is time and tasks remaining
        while cursor + block_len <= gap_end and tasks:
            current_task = tasks[0]
            
            # if task has no minutes left, move to next task
            if current_task.estimated_minutes <= 0:
                tasks.pop(0)
                continue
            
            # place a study block
            study_end = cursor + block_len
            
            weekly_grid[day].append({
                "start": cursor.time(),
                "end": study_end.time(),
                "category": f"study: {current_task.title}"
            })
            
            # subtract minutes
            current_task.estimated_minutes -= prefs.study_block_minutes
            
            # advance cursor
            cursor = study_end
            
def try_place_one_study_block(day, weekly_grid, task, prefs):
    """
    Try to place ONE study block for a single task somewhere in today's open slots.
    Returns True if placed, False otherwise.
    """
    
    gaps = find_open_slots_for_day(day, weekly_grid[day], prefs)
    
    study_len = timedelta(minutes=prefs.study_block_minutes)
    break_len = timedelta(minutes=prefs.break_minutes)
    
    for gap_start_t, gap_end_t in gaps:
        gap_start = datetime.combine(day, gap_start_t)
        gap_end = datetime.combine(day, gap_end_t)
        
        cursor = gap_start
        
        # need enough room for study + break (break optional at end)
        if cursor + study_len <= gap_end:
            study_end = cursor + study_len
            
            weekly_grid[day].append({
                "start": cursor.time(),
                "end": study_end.time(),
                "category": f"study: {task.title}"
            })
            
            task.estimated_minutes -= prefs.study_block_minutes
            
            # add a break block too (only if it fits in the gap)
            break_end = study_end + break_len
            if break_len.total_seconds() > 0 and break_end <= gap_end:
                weekly_grid[day].append({
                    "start": study_end.time(),
                    "end": break_end.time(),
                    "category": "break"
                })
                
            return True
    return False

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

    # build list of 7 dates starting monday
    week_dates = [monday + timedelta(days = i) for i in range(7)]

    # dictionary form
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

    # place fixed events (classes, appointments, shifts, etc.)
    for event in events:
        event_day = event.date
        if event_day not in weekly_grid:
            continue    #skip over days that are outside 7-day range

        # build datetime versions of event start/end
        event_start_dt = datetime.combine(event_day, event.start_time)
        event_end_dt = datetime.combine(event_day, event.end_time)

        # checking for overlaps
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
            
    # sort blocks for each day
    for day, blocks in weekly_grid.items():
        weekly_grid[day] = sorted(blocks, key = lambda b: b["start"])
        
    # show open slots (debug)
    for day, blocks in weekly_grid.items():
        gaps = find_open_slots_for_day(day, blocks, prefs)
        if gaps:
            formatted = ", ".join(
                f"{s.strftime('%H:%M')} - {e.strftime('%H:%M')}"
                for s, e in gaps
            )
            print(f"Open slots on {day}: {formatted}")
            
    # place study blocks into those open slots
    task_queue = sort_tasks_for_scheduling(tasks)
    
    # keep looping days until no more progress is possible or tasks finish
    progress = True
    while progress and task_queue:
        progress = False
        
        for day in weekly_grid:
            if not task_queue:
                break
        
            # remove tasks already completed
            task_queue = [t for t in task_queue if t.estimated_minutes > 0]
            if not task_queue:
                break
            
            # attempt: place ONE vlock for the highest-priority remaining task
            task = task_queue[0]
            placed = try_place_one_study_block(day, weekly_grid, task, prefs)
            
            if placed:
                progress = True
                
                # rotate to the back so we spread work across tasks + days
                task_queue = task_queue[1:] + [task]
        
        
    # re-sort again because of the just appened new blocks (study)
    for day, blocks in weekly_grid.items():
        weekly_grid[day] = sorted(blocks, key=lambda b: b["start"])
    
    # print readable schedule
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
            date = date(2025, 12, 15),
            start_time = time(9, 0),
            end_time = time(10, 0),
            category = "class"
        ),
    ]
    
    tasks = [
        Task(
            title = "Study for COMP 232 Quiz",
            course = "COMP 232",
            estimated_minutes = 180,
            priority = 5,
            due_date = date(2025, 12, 20)
        )
    ]
    goals = WellnessGoal(min_sleep_hours_per_day = 7, workouts_per_week = 3, meals_per_day = 3, self_care_blocks_per_week = 2)
    prefs = Preferences(earliest_start = time(8, 0), latest_end = time(22, 0), study_block_minutes = 60, break_minutes = 15)
    
    generate_weekly_plan(events, tasks, goals, prefs)