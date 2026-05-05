import os
import logging
from datetime import date
from typing import Dict, List, Optional

import anthropic

from .scoring import score_week, print_score_report
from .rules import run_all_rules, print_rules_report
from .models import Preferences

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 1024


# schedule serialiser
def serialise_schedule(weekly_grid: Dict[date, List[dict]]) -> str:
    """Convert the weekly grid into a readable text block for the model."""
    lines = ["WEEKLY SCHEDULE", "=" * 40]
    for day, blocks in weekly_grid.items():
        lines.append(f"\n{day.strftime('%A, %B %d')}:")
        if not blocks:
            lines.append("  (no activities scheduled)")
        for block in blocks:
            start = block["start"].strftime("%H:%M")
            end = block["end"].strftime("%H:%M")
            category = block["category"].capitalize()
            lines.append(f"  {start} - {end}  {category}")
    return "\n".join(lines)


def serialise_score(score: dict) -> str:
    """Convert the score report into readable text for the model."""
    lines = ["BALANCE SCORE REPORT", "=" * 40]
    for day, ds in score["days"].items():
        lines.append(
            f"{day.strftime('%A'):12}  "
            f"study: {ds['study_minutes']:5.0f}m  "
            f"wellness: {ds['wellness_minutes']:5.0f}m  "
            f"free: {ds['free_minutes']:5.0f}m  "
            f"balance: {ds['balance_score']:.2f}"
        )
    lines.append(f"\nOverall weekly balance score: {score['weekly_balance_score']:.2f} / 1.00")
    lines.append(f"Total study: {score['total_study_minutes']:.0f}m  "
                 f"wellness: {score['total_wellness_minutes']:.0f}m  "
                 f"free: {score['total_free_minutes']:.0f}m")
    return "\n".join(lines)


def serialise_violations(violations: dict) -> str:
    """Convert rule violations into readable text for the model."""
    if not violations:
        return "RULE VIOLATIONS\n" + "=" * 40 + "\nNo violations found."
    lines = ["RULE VIOLATIONS", "=" * 40]
    for day, vs in violations.items():
        lines.append(f"\n{day.strftime('%A, %B %d')}:")
        for v in vs:
            lines.append(f"  - {v}")
    return "\n".join(lines)


# system prompt builder
def build_system_prompt(
    weekly_grid: Dict[date, List[dict]],
    prefs: Preferences,
) -> str:
    """
    Build the full system prompt by injecting the schedule, score,
    and rule violations as context.
    """
    score = score_week(weekly_grid, prefs)
    violations = run_all_rules(weekly_grid, prefs)

    schedule_text = serialise_schedule(weekly_grid)
    score_text = serialise_score(score)
    violations_text = serialise_violations(violations)

    return f"""You are an AI well-being mentor for a university student.
You have been given the student's generated weekly schedule, their balance score report,
and any rule violations detected in the schedule.

Your role is to:
- Explain the schedule in plain, friendly English
- Suggest specific, actionable improvements to balance
- Answer questions the student has about their schedule
- Suggest concrete adjustments when asked (e.g. "move workouts to mornings")

Always be encouraging and constructive. Keep responses concise and practical.
Reference specific days and times from the schedule when giving advice.

---

{schedule_text}

---

{score_text}

---

{violations_text}
"""


# mentor interface
def ask_mentor(
    question: str,
    weekly_grid: Dict[date, List[dict]],
    prefs: Preferences,
    conversation_history: Optional[List[dict]] = None,
) -> tuple[str, List[dict]]:
    """
    Send a question to the AI mentor with full schedule context.

    Args:
        question: The student's question or request.
        weekly_grid: The generated weekly schedule.
        prefs: User preferences (used for scoring and rule checking).
        conversation_history: Prior turns as list of {role, content} dicts.
                              Pass None or [] to start a fresh conversation.

    Returns:
        (answer, updated_history) — the model's response and the full
        conversation history including this turn, ready to pass back in
        for the next turn.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY environment variable is not set. "
            "Run: export ANTHROPIC_API_KEY=your_key"
        )

    client = anthropic.Anthropic(api_key=api_key)
    system_prompt = build_system_prompt(weekly_grid, prefs)

    history = list(conversation_history or [])
    history.append({"role": "user", "content": question})

    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=system_prompt,
        messages=history,
    )

    answer = response.content[0].text
    history.append({"role": "assistant", "content": answer})

    logger.info("Mentor responded (%d tokens used).", response.usage.output_tokens)
    return answer, history


def get_schedule_summary(
    weekly_grid: Dict[date, List[dict]],
    prefs: Preferences,
) -> tuple[str, List[dict]]:
    """
    Convenience function — asks the mentor to explain the schedule
    in plain English without the user needing to type anything.
    Returns (summary, history) so the conversation can continue.
    """
    return ask_mentor(
        question=(
            "Please give me a friendly overview of my weekly schedule. "
            "Highlight the balance between study, wellness, and free time, "
            "and flag anything that looks off."
        ),
        weekly_grid=weekly_grid,
        prefs=prefs,
        conversation_history=None,
    )