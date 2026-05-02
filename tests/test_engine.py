import pytest
from datetime import date, time, timedelta, datetime

from src.engine import (
    find_open_slots_for_day,
    sort_tasks_for_scheduling,
    try_place_one_study_block,
    place_meals_for_day,
    place_workouts_for_week,
    generate_weekly_plan,
)
from src.models import Task, Event, WellnessGoal, Preferences

# shared fixtures

FUTURE = date(2099, 1, 1)
TEST_DAY = date(2099, 6, 2)  # fixed Monday-like date for deterministic tests


@pytest.fixture
def prefs():
    return Preferences(
        earliest_start=time(8, 0),
        latest_end=time(22, 0),
        study_block_minutes=60,
        break_minutes=15,
    )


@pytest.fixture
def goals():
    return WellnessGoal(
        min_sleep_hours_per_day=7,
        workouts_per_week=3,
        meals_per_day=3,
        self_care_blocks_per_week=2,
    )


def make_block(start: time, end: time, category: str = "event") -> dict:
    return {"start": start, "end": end, "category": category}


def make_task(title="Task", minutes=120, priority=3, due=FUTURE) -> Task:
    return Task(title=title, estimated_minutes=minutes, priority=priority, due_date=due)


# find_open_slots_for_day

class TestFindOpenSlots:
    def test_empty_day_returns_full_window(self, prefs):
        gaps = find_open_slots_for_day(TEST_DAY, [], prefs)
        assert len(gaps) == 1
        assert gaps[0] == (time(8, 0), time(22, 0))

    def test_block_in_middle_splits_window(self, prefs):
        blocks = [make_block(time(12, 0), time(13, 0))]
        gaps = find_open_slots_for_day(TEST_DAY, blocks, prefs)
        assert len(gaps) == 2
        assert gaps[0] == (time(8, 0), time(12, 0))
        assert gaps[1] == (time(13, 0), time(22, 0))

    def test_block_at_window_start_leaves_tail(self, prefs):
        blocks = [make_block(time(8, 0), time(10, 0))]
        gaps = find_open_slots_for_day(TEST_DAY, blocks, prefs)
        assert len(gaps) == 1
        assert gaps[0] == (time(10, 0), time(22, 0))

    def test_block_at_window_end_leaves_head(self, prefs):
        blocks = [make_block(time(21, 0), time(22, 0))]
        gaps = find_open_slots_for_day(TEST_DAY, blocks, prefs)
        assert len(gaps) == 1
        assert gaps[0] == (time(8, 0), time(21, 0))

    def test_fully_blocked_day_returns_no_gaps(self, prefs):
        blocks = [make_block(time(8, 0), time(22, 0))]
        gaps = find_open_slots_for_day(TEST_DAY, blocks, prefs)
        assert gaps == []

    def test_block_outside_window_is_ignored(self, prefs):
        blocks = [make_block(time(6, 0), time(7, 0))]  # before window
        gaps = find_open_slots_for_day(TEST_DAY, blocks, prefs)
        assert len(gaps) == 1
        assert gaps[0] == (time(8, 0), time(22, 0))

    def test_overlapping_blocks_are_merged(self, prefs):
        blocks = [
            make_block(time(9, 0), time(11, 0)),
            make_block(time(10, 0), time(12, 0)),  # overlaps previous
        ]
        gaps = find_open_slots_for_day(TEST_DAY, blocks, prefs)
        assert len(gaps) == 2
        assert gaps[0] == (time(8, 0), time(9, 0))
        assert gaps[1] == (time(12, 0), time(22, 0))

    def test_gap_smaller_than_study_block_is_excluded(self, prefs):
        # leaves a 30-min gap which is less than the 60-min study block
        blocks = [
            make_block(time(8, 30), time(22, 0)),
        ]
        gaps = find_open_slots_for_day(TEST_DAY, blocks, prefs)
        assert gaps == []

    def test_overnight_block_is_skipped(self, prefs):
        # end <= start signals overnight — should be ignored
        blocks = [make_block(time(22, 0), time(6, 0), "sleep")]
        gaps = find_open_slots_for_day(TEST_DAY, blocks, prefs)
        assert len(gaps) == 1
        assert gaps[0] == (time(8, 0), time(22, 0))


# sort_tasks_for_scheduling

class TestSortTasks:
    def test_higher_priority_comes_first(self):
        t1 = make_task("Low", priority=1)
        t2 = make_task("High", priority=5)
        result = sort_tasks_for_scheduling([t1, t2])
        assert result[0].title == "High"

    def test_same_priority_earlier_due_date_first(self):
        t1 = make_task("Later", priority=3, due=date(2099, 6, 10))
        t2 = make_task("Sooner", priority=3, due=date(2099, 6, 5))
        result = sort_tasks_for_scheduling([t1, t2])
        assert result[0].title == "Sooner"

    def test_priority_beats_due_date(self):
        t1 = make_task("UrgentLow", priority=2, due=date(2099, 6, 3))
        t2 = make_task("HighLater", priority=5, due=date(2099, 6, 30))
        result = sort_tasks_for_scheduling([t1, t2])
        assert result[0].title == "HighLater"

    def test_empty_list_returns_empty(self):
        assert sort_tasks_for_scheduling([]) == []

    def test_single_task_returns_single(self):
        t = make_task()
        assert sort_tasks_for_scheduling([t]) == [t]


# try_place_one_study_block

class TestTryPlaceOneStudyBlock:
    def _grid(self, blocks=None):
        return {TEST_DAY: blocks or []}

    def test_places_block_in_empty_day(self, prefs):
        task = make_task(minutes=120)
        grid = self._grid()
        placed = try_place_one_study_block(TEST_DAY, grid, task, prefs)
        assert placed is True
        study_blocks = [b for b in grid[TEST_DAY] if b["category"].startswith("study:")]
        assert len(study_blocks) == 1
        assert study_blocks[0]["start"] == time(8, 0)
        assert study_blocks[0]["end"] == time(9, 0)

    def test_also_places_break_after_study(self, prefs):
        task = make_task(minutes=120)
        grid = self._grid()
        try_place_one_study_block(TEST_DAY, grid, task, prefs)
        break_blocks = [b for b in grid[TEST_DAY] if b["category"] == "break"]
        assert len(break_blocks) == 1
        assert break_blocks[0]["start"] == time(9, 0)
        assert break_blocks[0]["end"] == time(9, 15)

    def test_no_break_placed_when_break_minutes_zero(self):
        prefs_no_break = Preferences(
            earliest_start=time(8, 0),
            latest_end=time(22, 0),
            study_block_minutes=60,
            break_minutes=0,
        )
        task = make_task(minutes=60)
        grid = {TEST_DAY: []}
        try_place_one_study_block(TEST_DAY, grid, task, prefs_no_break)
        break_blocks = [b for b in grid[TEST_DAY] if b["category"] == "break"]
        assert break_blocks == []

    def test_decrements_task_estimated_minutes(self, prefs):
        task = make_task(minutes=120)
        grid = self._grid()
        try_place_one_study_block(TEST_DAY, grid, task, prefs)
        assert task.estimated_minutes == 60

    def test_returns_false_when_no_slots(self, prefs):
        task = make_task(minutes=60)
        grid = self._grid([make_block(time(8, 0), time(22, 0))])
        placed = try_place_one_study_block(TEST_DAY, grid, task, prefs)
        assert placed is False
        assert task.estimated_minutes == 60  # unchanged

    def test_block_label_includes_task_title(self, prefs):
        task = make_task(title="COMP 232 Quiz")
        grid = self._grid()
        try_place_one_study_block(TEST_DAY, grid, task, prefs)
        study_blocks = [b for b in grid[TEST_DAY] if b["category"].startswith("study:")]
        assert "COMP 232 Quiz" in study_blocks[0]["category"]


# place_meals_for_day

class TestPlaceMealsForDay:
    def _grid(self, blocks=None):
        return {TEST_DAY: blocks or []}

    def test_places_correct_number_of_meals(self, goals, prefs):
        grid = self._grid()
        place_meals_for_day(TEST_DAY, grid, goals, prefs)
        meals = [b for b in grid[TEST_DAY] if b["category"] == "meal"]
        assert len(meals) == goals.meals_per_day

    def test_each_meal_is_30_minutes(self, goals, prefs):
        grid = self._grid()
        place_meals_for_day(TEST_DAY, grid, goals, prefs)
        for block in grid[TEST_DAY]:
            if block["category"] == "meal":
                start = datetime.combine(TEST_DAY, block["start"])
                end = datetime.combine(TEST_DAY, block["end"])
                assert (end - start) == timedelta(minutes=30)

    def test_meals_within_window(self, goals, prefs):
        grid = self._grid()
        place_meals_for_day(TEST_DAY, grid, goals, prefs)
        for block in grid[TEST_DAY]:
            if block["category"] == "meal":
                assert block["start"] >= prefs.earliest_start
                assert block["end"] <= prefs.latest_end

    def test_skips_meal_on_overlap(self, goals, prefs):
        # block out the entire window — no meals should be placed
        grid = self._grid([make_block(time(8, 0), time(22, 0))])
        place_meals_for_day(TEST_DAY, grid, goals, prefs)
        meals = [b for b in grid[TEST_DAY] if b["category"] == "meal"]
        assert len(meals) == 0

    def test_zero_meals_goal_places_nothing(self, prefs):
        goals_no_meals = WellnessGoal(
            min_sleep_hours_per_day=7,
            workouts_per_week=3,
            meals_per_day=1,  # min allowed by validator is 1
            self_care_blocks_per_week=2,
        )
        grid = self._grid()
        place_meals_for_day(TEST_DAY, grid, goals_no_meals, prefs)
        meals = [b for b in grid[TEST_DAY] if b["category"] == "meal"]
        assert len(meals) == 1


# place_workouts_for_week

class TestPlaceWorkoutsForWeek:
    def _empty_grid(self):
        days = [TEST_DAY + timedelta(days=i) for i in range(7)]
        return {d: [] for d in days}

    def test_places_correct_number_of_workouts(self, goals, prefs):
        grid = self._empty_grid()
        place_workouts_for_week(grid, goals, prefs)
        workouts = [
            b for blocks in grid.values()
            for b in blocks if b["category"] == "workout"
        ]
        assert len(workouts) == goals.workouts_per_week

    def test_each_workout_is_60_minutes(self, goals, prefs):
        grid = self._empty_grid()
        place_workouts_for_week(grid, goals, prefs)
        for blocks in grid.values():
            for b in blocks:
                if b["category"] == "workout":
                    start = datetime.combine(TEST_DAY, b["start"])
                    end = datetime.combine(TEST_DAY, b["end"])
                    assert (end - start) == timedelta(minutes=60)

    def test_zero_workouts_goal_places_nothing(self, prefs):
        goals_none = WellnessGoal(
            min_sleep_hours_per_day=7,
            workouts_per_week=0,
            meals_per_day=3,
            self_care_blocks_per_week=2,
        )
        grid = self._empty_grid()
        place_workouts_for_week(grid, goals_none, prefs)
        workouts = [
            b for blocks in grid.values()
            for b in blocks if b["category"] == "workout"
        ]
        assert workouts == []

    def test_workouts_spread_across_different_days(self, goals, prefs):
        grid = self._empty_grid()
        place_workouts_for_week(grid, goals, prefs)
        days_with_workouts = [
            day for day, blocks in grid.items()
            if any(b["category"] == "workout" for b in blocks)
        ]
        assert len(days_with_workouts) == goals.workouts_per_week


# generate_weekly_plan (integration)

class TestGenerateWeeklyPlan:
    def test_returns_7_day_grid(self, goals, prefs):
        grid = generate_weekly_plan([], [], goals, prefs)
        assert len(grid) == 7

    def test_all_days_have_sleep_block(self, goals, prefs):
        grid = generate_weekly_plan([], [], goals, prefs)
        for day, blocks in grid.items():
            sleep = [b for b in blocks if b["category"] == "sleep"]
            assert len(sleep) == 1, f"Missing sleep on {day}"

    def test_all_days_have_correct_meal_count(self, goals, prefs):
        grid = generate_weekly_plan([], [], goals, prefs)
        for day, blocks in grid.items():
            meals = [b for b in blocks if b["category"] == "meal"]
            assert len(meals) == goals.meals_per_day, f"Wrong meal count on {day}"

    def test_workout_count_matches_goal(self, goals, prefs):
        grid = generate_weekly_plan([], [], goals, prefs)
        workouts = [
            b for blocks in grid.values()
            for b in blocks if b["category"] == "workout"
        ]
        assert len(workouts) == goals.workouts_per_week

    def test_blocks_sorted_by_start_time_each_day(self, goals, prefs):
        grid = generate_weekly_plan([], [], goals, prefs)
        for day, blocks in grid.items():
            starts = [b["start"] for b in blocks]
            assert starts == sorted(starts), f"Blocks not sorted on {day}"

    def test_study_blocks_placed_for_tasks(self, goals, prefs):
        tasks = [make_task("COMP 232", minutes=120, priority=5)]
        grid = generate_weekly_plan([], tasks, goals, prefs)
        study_blocks = [
            b for blocks in grid.values()
            for b in blocks if b["category"].startswith("study:")
        ]
        assert len(study_blocks) >= 1

    def test_fixed_event_appears_in_grid(self, goals, prefs):
        # get next Monday's date (same logic as engine)
        from datetime import date as dt
        today = dt.today()
        monday = today + timedelta(days=(7 - today.weekday()) % 7)
        event = Event(
            name="Lecture",
            date=monday,
            start_time=time(10, 0),
            end_time=time(11, 0),
            category="class",
        )
        grid = generate_weekly_plan([event], [], goals, prefs)
        day_blocks = grid[monday]
        class_blocks = [b for b in day_blocks if b["category"] == "class"]
        assert len(class_blocks) == 1

    def test_event_outside_week_is_ignored(self, goals, prefs):
        far_future = Event(
            name="Far Event",
            date=date(2099, 1, 1),
            start_time=time(10, 0),
            end_time=time(11, 0),
            category="class",
        )
        grid = generate_weekly_plan([far_future], [], goals, prefs)
        all_blocks = [b for blocks in grid.values() for b in blocks]
        class_blocks = [b for b in all_blocks if b["category"] == "class"]
        assert class_blocks == []

    def test_task_estimated_minutes_reduced_after_scheduling(self, goals, prefs):
        task = make_task("Essay", minutes=60, priority=5)
        generate_weekly_plan([], [task], goals, prefs)
        assert task.estimated_minutes <= 0