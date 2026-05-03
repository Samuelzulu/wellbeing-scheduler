from datetime import datetime, date, time, timedelta
from typing import Dict, List


def check_no_study_after(blocks: List[dict], cutoff: time = time(21, 0)) -> List[str]:
    """Flag any study blocks that start at or after `cutoff`."""
    violations = []
    for block in blocks:
        if block["category"].lower().startswith("study:"):
            if block["start"] >= cutoff:
                violations.append(
                    f"Study block at {block['start'].strftime('%H:%M')} "
                    f"is at or after the {cutoff.strftime('%H:%M')} cutoff."
                )
    return violations


def check_no_back_to_back_study(blocks: List[dict]) -> List[str]:
    """
    Flag consecutive study blocks with no break between them.
    Expects blocks sorted by start time.
    """
    violations = []
    sorted_blocks = sorted(blocks, key=lambda b: b["start"])
    prev = None
    for block in sorted_blocks:
        if block["category"].lower().startswith("study:"):
            if prev is not None and block["start"] == prev["end"]:
                violations.append(
                    f"Back-to-back study blocks at "
                    f"{prev['start'].strftime('%H:%M')}–{block['end'].strftime('%H:%M')} "
                    f"with no break."
                )
            prev = block
        else:
            prev = None  # a non-study block resets the streak
    return violations


def check_minimum_free_time(blocks: List[dict], prefs, min_free_minutes: int = 60) -> List[str]:
    """Flag days where free time within the window is below `min_free_minutes`."""

    violations = []
    window_start = datetime.combine(date.today(), prefs.earliest_start)
    window_end = datetime.combine(date.today(), prefs.latest_end)
    window_minutes = (window_end - window_start).total_seconds() / 60

    scheduled_minutes = 0.0
    for block in blocks:
        start = datetime.combine(date.today(), block["start"])
        end = datetime.combine(date.today(), block["end"])
        duration = (end - start).total_seconds() / 60
        if duration > 0:
            scheduled_minutes += duration

    free_minutes = window_minutes - scheduled_minutes
    if free_minutes < min_free_minutes:
        violations.append(
            f"Only {free_minutes:.0f} free minutes in the day "
            f"(minimum is {min_free_minutes}m)."
        )
    return violations


def run_all_rules(weekly_grid: Dict[date, List[dict]], prefs, study_cutoff: time = time(21, 0), min_free_minutes: int = 60) -> Dict[date, List[str]]:
    """
    Run all rule checks across every day.
    Returns a dict of {date: [violation strings]}, only including days with violations.
    """
    report = {}
    for day, blocks in weekly_grid.items():
        violations = []
        violations += check_no_study_after(blocks, cutoff=study_cutoff)
        violations += check_no_back_to_back_study(blocks)
        violations += check_minimum_free_time(blocks, prefs, min_free_minutes=min_free_minutes)
        if violations:
            report[day] = violations
    return report


def print_rules_report(report: Dict[date, List[str]]) -> None:
    """Print a human-readable rules violation report."""
    print("\n==================== RULES VIOLATIONS ====================\n")
    if not report:
        print("  No violations found.\n")
        return
    for day, violations in report.items():
        print(f"  {day.strftime('%A, %B %d')}:")
        for v in violations:
            print(f"    - {v}")
    print()