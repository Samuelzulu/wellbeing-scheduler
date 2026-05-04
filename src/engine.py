import logging
from datetime import datetime, time, timedelta, date
from typing import Dict, List, Tuple

from .models import Event, Task, WellnessGoal, Preferences

logger = logging.getLogger(__name__)

# find_open_slots_for_day
def find_open_slots_for_day(day: date, blocks: List[dict], prefs: Preferences) -> List[Tuple[time, time]]:
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
            
    # find gaps between merged occupied intervals
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
        
# sort_tasks_for_scheduling
def sort_tasks_for_scheduling(tasks: List[Task]) -> List[Task]:
    # priority: higher first, due_date: earlier first
    return sorted(tasks, key=lambda t: (-t.priority, t.due_date))

# place_study_for_day
def place_study_for_day(day: date, weekly_grid: Dict[date, List[dict]], tasks: List[Task], prefs: Preferences) -> None:
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
            
# try_place_one_study_block
def try_place_one_study_block(day: date, weekly_grid: Dict[date, List[dict]], task: Task, prefs: Preferences) -> bool:
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

# place_meals_for_day
def place_meals_for_day(day: date, weekly_grid: Dict[date, List[dict]], goals: WellnessGoal, prefs: Preferences) -> None:
    """
    Place evenly-spaced meal blocks across the day window.
    Each meal block is 30 minutes. Skips the slot if it overlaps an existing block.
    """
    if goals.meals_per_day < 1:
        return

    window_start = datetime.combine(day, prefs.earliest_start)
    window_end = datetime.combine(day, prefs.latest_end)
    window_minutes = (window_end - window_start).total_seconds() / 60
    meal_duration = timedelta(minutes=30)

    # space meals evenly across the window
    interval = window_minutes / (goals.meals_per_day + 1)

    for i in range(1, goals.meals_per_day + 1):
        meal_start = window_start + timedelta(minutes=interval * i)
        meal_end = meal_start + meal_duration

        # clamp to window
        if meal_end > window_end:
            meal_end = window_end
            meal_start = meal_end - meal_duration

        # skip if overlaps any existing block
        overlap = False
        for block in weekly_grid[day]:
            block_start = datetime.combine(day, block["start"])
            block_end = datetime.combine(day, block["end"])
            if not (meal_end <= block_start or meal_start >= block_end):
                overlap = True
                break

        if not overlap:
            weekly_grid[day].append({
                "start": meal_start.time(),
                "end": meal_end.time(),
                "category": "meal"
            })


# place_workouts_for_week
def place_workouts_for_week(weekly_grid: Dict[date, List[dict]], goals: WellnessGoal, prefs: Preferences) -> None:
    """
    Distribute workout blocks across the week, aiming for goals.workouts_per_week.
    Each workout is 60 minutes. Placed in the first available slot on each day,
    spacing them out by skipping days that already have a workout.
    """
    if goals.workouts_per_week < 1:
        return

    workout_duration = timedelta(minutes=60)
    placed = 0
    days = list(weekly_grid.keys())

    # spread workouts evenly: pick every Nth day
    step = max(1, len(days) // goals.workouts_per_week)

    for i in range(0, len(days), step):
        if placed >= goals.workouts_per_week:
            break

        day = days[i]
        gaps = find_open_slots_for_day(day, weekly_grid[day], prefs)

        for gap_start_t, gap_end_t in gaps:
            gap_start = datetime.combine(day, gap_start_t)
            gap_end = datetime.combine(day, gap_end_t)

            if gap_start + workout_duration <= gap_end:
                workout_end = gap_start + workout_duration
                weekly_grid[day].append({
                    "start": gap_start.time(),
                    "end": workout_end.time(),
                    "category": "workout"
                })
                placed += 1
                break

# generate_weekly_plan
def generate_weekly_plan(
        events: List[Event],
        tasks: List[Task],
        goals: WellnessGoal,
        prefs: Preferences,
) -> Dict[date, List[dict]]:
    """
    Generate a weekly schedule plan based on user input.
    Steps:
        1. Create weekly time grid (7 days from this Monday)
        2. Place sleep blocks
        3. Place fixed events (with overlap detection)
        4. Place meals and workouts
        5. Place study blocks in remaining open slots
    """
    today = date.today()

    # how many days until next Monday
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
                logger.warning("Overlap detected on %s: '%s' conflicts with '%s' — skipping.", event_day, event.name, block['category'])
                break

        # add event only if no overlap
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
            
    # place meals and workouts before study so they get priority slots
    for day in weekly_grid:
        place_meals_for_day(day, weekly_grid, goals, prefs)
    place_workouts_for_week(weekly_grid, goals, prefs)

    # re-sort after meals/workouts
    for day, blocks in weekly_grid.items():
        weekly_grid[day] = sorted(blocks, key=lambda b: b["start"])

    # place study blocks into remaining open slots
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
            
            # attempt: place ONE block for the highest-priority remaining task
            task = task_queue[0]
            placed = try_place_one_study_block(day, weekly_grid, task, prefs)
            
            if placed:
                progress = True
                
                # rotate to the back so we spread work across tasks + days
                task_queue = task_queue[1:] + [task]
        
        
    # re-sort again after newly appended study blocks
    for day, blocks in weekly_grid.items():
        weekly_grid[day] = sorted(blocks, key=lambda b: b["start"])
    
    # print readable schedule
    return weekly_grid

# print_schedule
def print_schedule(weekly_grid: Dict[date, List[dict]]) -> None:
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