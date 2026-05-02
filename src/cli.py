import typer
from datetime import date, time
from typing import List

from .models import Event, Task, WellnessGoal, Preferences
from .engine import generate_weekly_plan
from .scoring import score_week, print_score_report
from .rules import run_all_rules, print_rules_report

app = typer.Typer(help="Student well-being scheduler — generate your weekly plan.", add_completion=False)
app = typer.Typer(help="Student well-being scheduler — generate your weekly plan.", invoke_without_command=False)


@app.command("plan")
def plan(
    sleep: float = typer.Option(7.0, help="Minimum sleep hours per day"),
    workouts: int = typer.Option(3, help="Workouts per week"),
    meals: int = typer.Option(3, help="Meals per day"),
    self_care: int = typer.Option(2, help="Self-care blocks per week"),
    earliest: str = typer.Option("08:00", help="Earliest start time (HH:MM)"),
    latest: str = typer.Option("22:00", help="Latest end time (HH:MM)"),
    block: int = typer.Option(60, help="Study block length in minutes"),
    break_mins: int = typer.Option(15, help="Break length after each study block"),
    score: bool = typer.Option(False, "--score", help="Print balance score report"),
    rules: bool = typer.Option(False, "--rules", help="Print rules violation report"),
):
    """Generate a weekly schedule and print it to the terminal."""

    def _parse_time(s: str) -> time:
        h, m = map(int, s.split(":"))
        return time(h, m)

    goals = WellnessGoal(
        min_sleep_hours_per_day=sleep,
        workouts_per_week=workouts,
        meals_per_day=meals,
        self_care_blocks_per_week=self_care,
    )
    prefs = Preferences(
        earliest_start=_parse_time(earliest),
        latest_end=_parse_time(latest),
        study_block_minutes=block,
        break_minutes=break_mins,
    )

    # placeholder: no events or tasks from CLI yet — add file input in a future phase
    events: List[Event] = []
    tasks: List[Task] = []

    weekly_grid = generate_weekly_plan(events, tasks, goals, prefs)

    if score:
        report = score_week(weekly_grid, prefs)
        print_score_report(report)

    if rules:
        violations = run_all_rules(weekly_grid, prefs)
        print_rules_report(violations)


def main():
    app()


if __name__ == "__main__":
    main()