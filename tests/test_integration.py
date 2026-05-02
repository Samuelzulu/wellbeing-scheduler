"""
End-to-end integration tests: scoring and rules work correctly
on a real grid produced by generate_weekly_plan.
"""
import pytest
from datetime import date, time, timedelta

from src.engine import generate_weekly_plan
from src.models import Task, WellnessGoal, Preferences
from src.scoring import score_week, score_day
from src.rules import (
    run_all_rules,
    check_no_study_after,
    check_no_back_to_back_study,
    check_minimum_free_time,
)

FUTURE = date(2099, 1, 1)


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


@pytest.fixture
def grid(goals, prefs):
    tasks = [
        Task(title="COMP 232", estimated_minutes=180, priority=5, due_date=FUTURE),
        Task(title="MATH 101", estimated_minutes=120, priority=3, due_date=FUTURE),
    ]
    return generate_weekly_plan([], tasks, goals, prefs)


# scoring integration

class TestScoringIntegration:
    def test_score_week_returns_all_7_days(self, grid, prefs):
        report = score_week(grid, prefs)
        assert len(report["days"]) == 7

    def test_weekly_balance_score_between_0_and_1(self, grid, prefs):
        report = score_week(grid, prefs)
        assert 0.0 <= report["weekly_balance_score"] <= 1.0

    def test_total_study_minutes_positive_when_tasks_given(self, grid, prefs):
        report = score_week(grid, prefs)
        assert report["total_study_minutes"] > 0

    def test_total_wellness_minutes_positive(self, grid, prefs):
        report = score_week(grid, prefs)
        assert report["total_wellness_minutes"] > 0

    def test_score_day_keys_present(self, grid, prefs):
        first_day = list(grid.keys())[0]
        result = score_day(grid[first_day], prefs)
        assert "study_minutes" in result
        assert "wellness_minutes" in result
        assert "free_minutes" in result
        assert "balance_score" in result

    def test_score_day_balance_between_0_and_1(self, grid, prefs):
        for blocks in grid.values():
            result = score_day(blocks, prefs)
            assert 0.0 <= result["balance_score"] <= 1.0

    def test_empty_day_has_zero_study(self, prefs):
        result = score_day([], prefs)
        assert result["study_minutes"] == 0.0


# rules integration

class TestRulesIntegration:
    def test_run_all_rules_returns_dict(self, grid, prefs):
        report = run_all_rules(grid, prefs)
        assert isinstance(report, dict)

    def test_no_study_after_cutoff_clean_schedule(self, grid, prefs):
        # default schedule should have no late-night study
        report = run_all_rules(grid, prefs, study_cutoff=time(21, 0))
        for day, violations in report.items():
            late_study = [v for v in violations if "cutoff" in v]
            assert late_study == [], f"Late study violation on {day}"

    def test_check_no_study_after_catches_violation(self, prefs):
        late_block = {"start": time(21, 30), "end": time(22, 30), "category": "study: Algo"}
        violations = check_no_study_after([late_block], cutoff=time(21, 0))
        assert len(violations) == 1
        assert "21:30" in violations[0]

    def test_check_no_study_after_no_violation_before_cutoff(self, prefs):
        early_block = {"start": time(9, 0), "end": time(10, 0), "category": "study: Algo"}
        violations = check_no_study_after([early_block], cutoff=time(21, 0))
        assert violations == []

    def test_check_back_to_back_catches_violation(self):
        blocks = [
            {"start": time(9, 0), "end": time(10, 0), "category": "study: A"},
            {"start": time(10, 0), "end": time(11, 0), "category": "study: B"},
        ]
        violations = check_no_back_to_back_study(blocks)
        assert len(violations) == 1

    def test_check_back_to_back_ok_with_break_between(self):
        blocks = [
            {"start": time(9, 0), "end": time(10, 0), "category": "study: A"},
            {"start": time(10, 0), "end": time(10, 15), "category": "break"},
            {"start": time(10, 15), "end": time(11, 15), "category": "study: B"},
        ]
        violations = check_no_back_to_back_study(blocks)
        assert violations == []

    def test_check_minimum_free_time_catches_overloaded_day(self, prefs):
        # fill almost the entire window
        blocks = [{"start": time(8, 0), "end": time(21, 50), "category": "study: X"}]
        violations = check_minimum_free_time(blocks, prefs, min_free_minutes=60)
        assert len(violations) == 1

    def test_check_minimum_free_time_ok_with_enough_free(self, prefs):
        blocks = [{"start": time(8, 0), "end": time(12, 0), "category": "study: X"}]
        violations = check_minimum_free_time(blocks, prefs, min_free_minutes=60)
        assert violations == []