from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...database.session import get_db
from ...database.crud import get_plan, get_all_plans
from ...database.models import PlanBlockORM
from ...models import Preferences
from ...mentor import ask_mentor
from ..schemas import MentorRequest, MentorResponse, ConversationMessage

router = APIRouter(prefix="/mentor", tags=["mentor"])


def _blocks_to_grid(plan) -> dict:
    """Reconstruct a weekly_grid dict from a persisted plan's blocks."""
    from datetime import datetime
    grid = {}
    for block in plan.blocks:
        day = block.day
        if day not in grid:
            grid[day] = []
        grid[day].append({
            "start": block.start_time,
            "end": block.end_time,
            "category": block.category,
        })
    # sort each day
    for day in grid:
        grid[day] = sorted(grid[day], key=lambda b: b["start"])
    return grid


def _default_prefs() -> Preferences:
    """Return standard preferences for scoring/rules when re-evaluating a saved plan."""
    from datetime import time
    return Preferences(
        earliest_start=time(8, 0),
        latest_end=time(22, 0),
        study_block_minutes=60,
        break_minutes=15,
    )


@router.post("/advice", response_model=MentorResponse)
def get_advice(payload: MentorRequest, db: Session = Depends(get_db)) -> MentorResponse:
    """
    Ask the AI mentor a question about a saved plan.
    If plan_id is omitted, uses the most recently created plan.
    Accepts optional conversation_history for multi-turn conversations.
    """
    # resolve which plan to use
    if payload.plan_id is not None:
        plan = get_plan(db, payload.plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
    else:
        all_plans = get_all_plans(db)
        if not all_plans:
            raise HTTPException(
                status_code=404,
                detail="No plans found. Generate a plan first via POST /plans/generate"
            )
        plan = all_plans[0]  # get_all_plans returns newest first

    # reconstruct grid and prefs
    weekly_grid = _blocks_to_grid(plan)
    prefs = _default_prefs()

    # convert schema history to plain dicts for the mentor
    history = [
        {"role": msg.role, "content": msg.content}
        for msg in (payload.conversation_history or [])
    ]

    # call the mentor
    try:
        answer, updated_history = ask_mentor(
            question=payload.question,
            weekly_grid=weekly_grid,
            prefs=prefs,
            conversation_history=history,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    # convert history back to schema format
    history_response = [
        ConversationMessage(role=msg["role"], content=msg["content"])
        for msg in updated_history
    ]

    return MentorResponse(
        answer=answer,
        conversation_history=history_response,
        plan_id=plan.id,
    )