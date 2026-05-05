from unittest.mock import MagicMock, patch
from datetime import date, time

import pytest

from src.mentor import (
    serialise_schedule,
    serialise_score,
    serialise_violations,
    build_system_prompt,
    ask_mentor,
    get_schedule_summary,
)
from src.models import Preferences

# fixtures
@pytest.fixture
def prefs():
    return Preferences(
        earliest_start=time(8, 0),
        latest_end=time(22, 0),
        study_block_minutes=60,
        break_minutes=15,
    )


@pytest.fixture
def sample_grid():
    day = date(2099, 6, 2)
    return {
        day: [
            {"start": time(8, 0),  "end": time(9, 0),  "category": "workout"},
            {"start": time(9, 0),  "end": time(10, 0), "category": "study: COMP 232"},
            {"start": time(12, 0), "end": time(12, 30),"category": "meal"},
            {"start": time(22, 0), "end": time(5, 0),  "category": "sleep"},
        ]
    }


@pytest.fixture
def mock_anthropic_response():
    """A fake Anthropic API response."""
    mock_content = MagicMock()
    mock_content.text = "Here is your schedule summary."

    mock_usage = MagicMock()
    mock_usage.output_tokens = 42

    mock_response = MagicMock()
    mock_response.content = [mock_content]
    mock_response.usage = mock_usage
    return mock_response


# serialise_schedule
class TestSerialiseSchedule:
    def test_contains_day_name(self, sample_grid):
        result = serialise_schedule(sample_grid)
        assert "Tuesday" in result

    def test_contains_block_categories(self, sample_grid):
        result = serialise_schedule(sample_grid)
        assert "Workout" in result
        assert "Meal" in result

    def test_contains_times(self, sample_grid):
        result = serialise_schedule(sample_grid)
        assert "08:00" in result
        assert "09:00" in result

    def test_empty_day_handled(self, prefs):
        grid = {date(2099, 6, 2): []}
        result = serialise_schedule(grid)
        assert "no activities" in result

    def test_returns_string(self, sample_grid):
        assert isinstance(serialise_schedule(sample_grid), str)


# serialise_score
class TestSerialiseScore:
    def test_contains_balance_score(self, sample_grid, prefs):
        from src.scoring import score_week
        score = score_week(sample_grid, prefs)
        result = serialise_score(score)
        assert "balance" in result.lower()

    def test_contains_weekly_total(self, sample_grid, prefs):
        from src.scoring import score_week
        score = score_week(sample_grid, prefs)
        result = serialise_score(score)
        assert "Overall weekly balance score" in result

    def test_returns_string(self, sample_grid, prefs):
        from src.scoring import score_week
        score = score_week(sample_grid, prefs)
        assert isinstance(serialise_score(score), str)


# serialise_violations
class TestSerialiseViolations:
    def test_no_violations_message(self):
        result = serialise_violations({})
        assert "No violations found" in result

    def test_violations_included(self):
        violations = {date(2099, 6, 2): ["Study block after cutoff."]}
        result = serialise_violations(violations)
        assert "Study block after cutoff." in result

    def test_returns_string(self):
        assert isinstance(serialise_violations({}), str)


# build_system_prompt
class TestBuildSystemPrompt:
    def test_contains_schedule_section(self, sample_grid, prefs):
        result = build_system_prompt(sample_grid, prefs)
        assert "WEEKLY SCHEDULE" in result

    def test_contains_score_section(self, sample_grid, prefs):
        result = build_system_prompt(sample_grid, prefs)
        assert "BALANCE SCORE REPORT" in result

    def test_contains_violations_section(self, sample_grid, prefs):
        result = build_system_prompt(sample_grid, prefs)
        assert "RULE VIOLATIONS" in result

    def test_contains_role_description(self, sample_grid, prefs):
        result = build_system_prompt(sample_grid, prefs)
        assert "well-being mentor" in result

    def test_returns_string(self, sample_grid, prefs):
        assert isinstance(build_system_prompt(sample_grid, prefs), str)


# ask_mentor
class TestAskMentor:
    def test_returns_answer_and_history(self, sample_grid, prefs, mock_anthropic_response):
        with patch("src.mentor.anthropic.Anthropic") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_anthropic_response
            mock_client_cls.return_value = mock_client

            with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
                answer, history = ask_mentor(
                    question="How is my schedule?",
                    weekly_grid=sample_grid,
                    prefs=prefs,
                )

        assert answer == "Here is your schedule summary."
        assert isinstance(history, list)

    def test_history_contains_user_and_assistant_turns(self, sample_grid, prefs, mock_anthropic_response):
        with patch("src.mentor.anthropic.Anthropic") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_anthropic_response
            mock_client_cls.return_value = mock_client

            with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
                _, history = ask_mentor(
                    question="How is my schedule?",
                    weekly_grid=sample_grid,
                    prefs=prefs,
                )

        roles = [msg["role"] for msg in history]
        assert "user" in roles
        assert "assistant" in roles

    def test_multi_turn_history_passed_to_api(self, sample_grid, prefs, mock_anthropic_response):
        prior_history = [
            {"role": "user", "content": "First question"},
            {"role": "assistant", "content": "First answer"},
        ]
        with patch("src.mentor.anthropic.Anthropic") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_anthropic_response
            mock_client_cls.return_value = mock_client

            with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
                _, history = ask_mentor(
                    question="Follow-up question",
                    weekly_grid=sample_grid,
                    prefs=prefs,
                    conversation_history=prior_history,
                )

        assert len(history) == 4  # 2 prior + 1 user + 1 assistant

    def test_raises_runtime_error_without_api_key(self, sample_grid, prefs):
        with patch.dict("os.environ", {}, clear=True):
            import os
            os.environ.pop("ANTHROPIC_API_KEY", None)
            with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
                ask_mentor(
                    question="How is my schedule?",
                    weekly_grid=sample_grid,
                    prefs=prefs,
                )

    def test_answer_is_string(self, sample_grid, prefs, mock_anthropic_response):
        with patch("src.mentor.anthropic.Anthropic") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_anthropic_response
            mock_client_cls.return_value = mock_client

            with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
                answer, _ = ask_mentor(
                    question="How is my schedule?",
                    weekly_grid=sample_grid,
                    prefs=prefs,
                )

        assert isinstance(answer, str)


# get_schedule_summary
class TestGetScheduleSummary:
    def test_returns_answer_and_history(self, sample_grid, prefs, mock_anthropic_response):
        with patch("src.mentor.anthropic.Anthropic") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_anthropic_response
            mock_client_cls.return_value = mock_client

            with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
                answer, history = get_schedule_summary(sample_grid, prefs)

        assert isinstance(answer, str)
        assert isinstance(history, list)

    def test_history_starts_with_user_turn(self, sample_grid, prefs, mock_anthropic_response):
        with patch("src.mentor.anthropic.Anthropic") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_anthropic_response
            mock_client_cls.return_value = mock_client

            with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
                _, history = get_schedule_summary(sample_grid, prefs)

        assert history[0]["role"] == "user"