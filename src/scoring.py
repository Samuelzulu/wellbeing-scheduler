from datetime import timedelta
from typing import Dict, List
import datetime


# minutes per category we consider "wellness"
WELLNESS_CATEGORIES = {"meal", "workout", "sleep"}
STUDY_PREFIX = "study:"


def _total_minutes(blocks: List[dict], category_filter=None) -> float:
    """Sum up block durations, optionally filtered by category prefix."""
    total = 0.0
    for block in blocks:
        cat = block["category"].lower()
        if category_filter is None or cat.startswith(category_filter) or cat == category_filter:
            start = datetime.datetime.combine(datetime.date.today(), block["start"])
            end = datetime.datetime.combine(datetime.date.today(), block["end"])
            duration = (end - start).total_seconds() / 60
            if duration > 0:
                total += duration
    return total


def score_day(blocks: List[dict], prefs) -> dict:
    """
    Score a single day's blocks. Returns a dict with:
      - study_minutes
      - wellness_minutes
      - free_minutes
      - balance_score  (0.0 – 1.0, higher is better)
    """
    window_start = datetime.datetime.combine(datetime.date.today(), prefs.earliest_start)
    window_end = datetime.datetime.combine(datetime.date.today(), prefs.latest_end)
    total_window = (window_end - window_start).total_seconds() / 60

    study_mins = _total_minutes(blocks, STUDY_PREFIX)
    wellness_mins = sum(_total_minutes(blocks, cat) for cat in WELLNESS_CATEGORIES)
    scheduled_mins = _total_minutes(blocks)
    free_mins = max(0.0, total_window - scheduled_mins)

    # balance: penalise days that are all-study or have zero wellness
    if total_window == 0:
        balance = 0.0
    else:
        study_ratio = study_mins / total_window
        wellness_ratio = wellness_mins / total_window
        free_ratio = free_mins / total_window

        # ideal rough targets: ~40% study, ~30% wellness, ~30% free
        study_score = 1.0 - abs(study_ratio - 0.40)
        wellness_score = 1.0 - abs(wellness_ratio - 0.30)
        free_score = 1.0 - abs(free_ratio - 0.30)
        balance = round((study_score + wellness_score + free_score) / 3, 3)

    return {
        "study_minutes": round(study_mins, 1),
        "wellness_minutes": round(wellness_mins, 1),
        "free_minutes": round(free_mins, 1),
        "balance_score": max(0.0, balance),
    }


def score_week(weekly_grid: Dict, prefs) -> dict:
    """
    Score the full weekly schedule. Returns per-day scores plus a weekly summary.
    """
    day_scores = {}
    total_study = 0.0
    total_wellness = 0.0
    total_free = 0.0
    balance_scores = []

    for day, blocks in weekly_grid.items():
        ds = score_day(blocks, prefs)
        day_scores[day] = ds
        total_study += ds["study_minutes"]
        total_wellness += ds["wellness_minutes"]
        total_free += ds["free_minutes"]
        balance_scores.append(ds["balance_score"])

    weekly_balance = round(sum(balance_scores) / len(balance_scores), 3) if balance_scores else 0.0

    return {
        "days": day_scores,
        "total_study_minutes": round(total_study, 1),
        "total_wellness_minutes": round(total_wellness, 1),
        "total_free_minutes": round(total_free, 1),
        "weekly_balance_score": weekly_balance,
    }


def print_score_report(score: dict) -> None:
    """Print a human-readable weekly score report."""
    print("\n==================== SCHEDULE SCORE REPORT ====================\n")
    for day, ds in score["days"].items():
        print(f"  {day.strftime('%A'):12}  study: {ds['study_minutes']:5.0f}m  "
              f"wellness: {ds['wellness_minutes']:5.0f}m  "
              f"free: {ds['free_minutes']:5.0f}m  "
              f"balance: {ds['balance_score']:.2f}")
    print()
    print(f"  Weekly totals —  study: {score['total_study_minutes']:.0f}m  "
          f"wellness: {score['total_wellness_minutes']:.0f}m  "
          f"free: {score['total_free_minutes']:.0f}m")
    print(f"  Overall balance score: {score['weekly_balance_score']:.2f} / 1.00")
    print()