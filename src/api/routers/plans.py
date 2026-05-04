from datetime import date, time, timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...database.session import get_db
from ...database.crud import create_plan, get_plan, get_all_plans
from ...database.models import TaskORM, EventORM
from ...models import (
    Task as TaskPydantic,
    Event as EventPydantic,
    WellnessGoal,
    Preferences,
)
from ...engine import generate_weekly_plan
from ...scoring import score_week
from ..schemas import PlanRequest, PlanResponse, PlanSummaryResponse

router = APIRouter(prefix="/plans", tags=["plans"])


def _parse_time(s: str) -> time:
    h, m = map(int, s.split(":"))
    return time(h, m)


def _orm_task_to_pydantic(t: TaskORM) -> TaskPydantic:
    return TaskPydantic(
        title=t.title,
        course=t.course,
        estimated_minutes=t.estimated_minutes,
        priority=t.priority,
        due_date=t.due_date,
        notes=t.notes,
    )


def _orm_event_to_pydantic(e: EventORM) -> EventPydantic:
    return EventPydantic(
        name=e.name,
        date=e.date,
        start_time=e.start_time,
        end_time=e.end_time,
        category=e.category,
    )


@router.post("/generate", response_model=PlanResponse,
             status_code=status.HTTP_201_CREATED)
def generate(payload: PlanRequest, db: Session = Depends(get_db)) -> PlanResponse:
    """
    Generate a weekly plan using all tasks and events currently in the database,
    then persist and return the result.
    """
    goals = WellnessGoal(
        min_sleep_hours_per_day=payload.sleep,
        workouts_per_week=payload.workouts,
        meals_per_day=payload.meals,
        self_care_blocks_per_week=payload.self_care,
    )
    prefs = Preferences(
        earliest_start=_parse_time(payload.earliest),
        latest_end=_parse_time(payload.latest),
        study_block_minutes=payload.block_minutes,
        break_minutes=payload.break_minutes,
    )

    # load tasks and events from DB, convert to Pydantic for the engine
    db_tasks = db.query(TaskORM).all()
    db_events = db.query(EventORM).all()
    tasks = [_orm_task_to_pydantic(t) for t in db_tasks]
    events = [_orm_event_to_pydantic(e) for e in db_events]

    weekly_grid = generate_weekly_plan(events, tasks, goals, prefs)

    # score the generated plan
    score = score_week(weekly_grid, prefs)
    balance_score = score["weekly_balance_score"]

    # flatten grid into a list of block dicts with a 'day' key for persistence
    flat_blocks = [
        {"day": day, "start": block["start"], "end": block["end"],
         "category": block["category"]}
        for day, blocks in weekly_grid.items()
        for block in blocks
    ]

    # determine week_start (Monday of this week)
    today = date.today()
    week_start = today + timedelta(days=(7 - today.weekday()) % 7)

    plan = create_plan(db, week_start=week_start, weekly_balance_score=balance_score, blocks=flat_blocks)
    return plan


@router.get("/", response_model=List[PlanSummaryResponse])
def list_all(db: Session = Depends(get_db)) -> List[PlanSummaryResponse]:
    return get_all_plans(db)


@router.get("/{plan_id}", response_model=PlanResponse)
def retrieve(plan_id: int, db: Session = Depends(get_db)) -> PlanResponse:
    plan = get_plan(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan