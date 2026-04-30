import pytest
from datetime import date, time
from pydantic import ValidationError

from src.models import Event, Task, WellnessGoal, Preferences

# helpers
FUTURE_DATE = date(2099, 12, 31)


# Event
class TestEvent:
    def test_valid_event(self):
        e = Event(
            name="COMP 232 Lecture",
            date=date(2025, 3, 10),
            start_time=time(9, 0),
            end_time=time(10, 0),
        )
        assert e.name == "COMP 232 Lecture"
        assert e.start_time < e.end_time

    def test_optional_category_defaults_none(self):
        e = Event(
            name="Lab",
            date=date(2025, 3, 10),
            start_time=time(13, 0),
            end_time=time(14, 0),
        )
        assert e.category is None

    def test_end_time_before_start_time_raises(self):
        with pytest.raises(ValidationError):
            Event(
                name="Bad event",
                date=date(2025, 3, 10),
                start_time=time(10, 0),
                end_time=time(9, 0),
            )

    def test_end_time_equal_to_start_time_raises(self):
        with pytest.raises(ValidationError):
            Event(
                name="Zero-length event",
                date=date(2025, 3, 10),
                start_time=time(10, 0),
                end_time=time(10, 0),
            )


# Task
class TestTask:
    def test_valid_task(self):
        t = Task(
            title="Study for COMP 232 Quiz",
            estimated_minutes=90,
            priority=3,
            due_date=FUTURE_DATE,
        )
        assert t.title == "Study for COMP 232 Quiz"
        assert t.priority == 3

    def test_optional_fields_default_none(self):
        t = Task(
            title="Read chapter",
            estimated_minutes=30,
            priority=2,
            due_date=FUTURE_DATE,
        )
        assert t.course is None
        assert t.notes is None

    def test_estimated_minutes_zero_raises(self):
        with pytest.raises(ValidationError):
            Task(title="X", estimated_minutes=0, priority=1, due_date=FUTURE_DATE)

    def test_estimated_minutes_negative_raises(self):
        with pytest.raises(ValidationError):
            Task(title="X", estimated_minutes=-10, priority=1, due_date=FUTURE_DATE)

    def test_priority_below_range_raises(self):
        with pytest.raises(ValidationError):
            Task(title="X", estimated_minutes=30, priority=0, due_date=FUTURE_DATE)

    def test_priority_above_range_raises(self):
        with pytest.raises(ValidationError):
            Task(title="X", estimated_minutes=30, priority=6, due_date=FUTURE_DATE)

    def test_priority_boundary_values_valid(self):
        for p in (1, 5):
            t = Task(title="X", estimated_minutes=30, priority=p, due_date=FUTURE_DATE)
            assert t.priority == p

    def test_due_date_in_past_raises(self):
        with pytest.raises(ValidationError):
            Task(
                title="X",
                estimated_minutes=30,
                priority=1,
                due_date=date(2000, 1, 1),
            )

    def test_estimated_minutes_mutable(self):
        """Engine subtracts from estimated_minutes — mutation must not raise."""
        t = Task(title="X", estimated_minutes=120, priority=1, due_date=FUTURE_DATE)
        t.estimated_minutes -= 60
        assert t.estimated_minutes == 60


# WellnessGoal
class TestWellnessGoal:
    def test_valid_goal(self):
        w = WellnessGoal(
            min_sleep_hours_per_day=7.5,
            workouts_per_week=3,
            meals_per_day=3,
            self_care_blocks_per_week=2,
        )
        assert w.min_sleep_hours_per_day == 7.5

    def test_zero_sleep_raises(self):
        with pytest.raises(ValidationError):
            WellnessGoal(
                min_sleep_hours_per_day=0,
                workouts_per_week=3,
                meals_per_day=3,
                self_care_blocks_per_week=2,
            )

    def test_negative_workouts_raises(self):
        with pytest.raises(ValidationError):
            WellnessGoal(
                min_sleep_hours_per_day=7,
                workouts_per_week=-1,
                meals_per_day=3,
                self_care_blocks_per_week=2,
            )

    def test_zero_meals_raises(self):
        with pytest.raises(ValidationError):
            WellnessGoal(
                min_sleep_hours_per_day=7,
                workouts_per_week=3,
                meals_per_day=0,
                self_care_blocks_per_week=2,
            )

    def test_negative_self_care_raises(self):
        with pytest.raises(ValidationError):
            WellnessGoal(
                min_sleep_hours_per_day=7,
                workouts_per_week=3,
                meals_per_day=3,
                self_care_blocks_per_week=-1,
            )

    def test_zero_workouts_and_self_care_allowed(self):
        """Zero is valid for optional wellness fields."""
        w = WellnessGoal(
            min_sleep_hours_per_day=8,
            workouts_per_week=0,
            meals_per_day=2,
            self_care_blocks_per_week=0,
        )
        assert w.workouts_per_week == 0
        assert w.self_care_blocks_per_week == 0


# Preferences
class TestPreferences:
    def test_valid_preferences(self):
        p = Preferences(
            earliest_start=time(8, 0),
            latest_end=time(22, 0),
            study_block_minutes=60,
            break_minutes=15,
        )
        assert p.study_block_minutes == 60

    def test_latest_end_before_earliest_start_raises(self):
        with pytest.raises(ValidationError):
            Preferences(
                earliest_start=time(22, 0),
                latest_end=time(8, 0),
                study_block_minutes=60,
                break_minutes=15,
            )

    def test_latest_end_equal_earliest_start_raises(self):
        with pytest.raises(ValidationError):
            Preferences(
                earliest_start=time(8, 0),
                latest_end=time(8, 0),
                study_block_minutes=60,
                break_minutes=15,
            )

    def test_zero_study_block_raises(self):
        with pytest.raises(ValidationError):
            Preferences(
                earliest_start=time(8, 0),
                latest_end=time(22, 0),
                study_block_minutes=0,
                break_minutes=15,
            )

    def test_negative_break_minutes_raises(self):
        with pytest.raises(ValidationError):
            Preferences(
                earliest_start=time(8, 0),
                latest_end=time(22, 0),
                study_block_minutes=60,
                break_minutes=-5,
            )

    def test_zero_break_minutes_allowed(self):
        """break_minutes=0 is valid (no break between study blocks)."""
        p = Preferences(
            earliest_start=time(8, 0),
            latest_end=time(22, 0),
            study_block_minutes=60,
            break_minutes=0,
        )
        assert p.break_minutes == 0