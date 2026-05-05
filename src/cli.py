# Usage: PYTHONPATH=. python3 -m src.cli --score --rules
# (Typer single-command mode — no subcommand needed)

import typer
from datetime import time
from typing import List

from .models import Event, Task, WellnessGoal, Preferences
from .engine import generate_weekly_plan
from .scoring import score_week, print_score_report
from .rules import run_all_rules, print_rules_report
from .mentor import ask_mentor

app = typer.Typer(
    help="Student well-being scheduler — generate your weekly plan.",
    add_completion=False,
)


@app.command()
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
    chat: bool = typer.Option(False, "--chat", help="Start interactive mentor chat after generating"),
) -> None:
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
    from .engine import print_schedule
    print_schedule(weekly_grid)

    if score:
        report = score_week(weekly_grid, prefs)
        print_score_report(report)

    if rules:
        violations = run_all_rules(weekly_grid, prefs)
        print_rules_report(violations)

    if chat:
        _run_chat(weekly_grid, prefs)

def _run_chat(weekly_grid: dict, prefs) -> None:
    """Interactive multi-turn mentor chat loop."""
    print("\n==================== AI MENTOR CHAT ====================")
    print("Ask anything about your schedule. Type 'quit' to exit.\n")

    history = []
    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting chat.")
            break

        if not question:
            continue
        if question.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break

        try:
            answer, history = ask_mentor(
                question=question,
                weekly_grid=weekly_grid,
                prefs=prefs,
                conversation_history=history,
            )
            print(f"\nMentor: {answer}\n")
        except RuntimeError as e:
            print(f"\nError: {e}\n")
            break
        except Exception as e:
            print(f"\nUnexpected error: {e}\n")
            break

def main() -> None:
    app()


if __name__ == "__main__":
    main()