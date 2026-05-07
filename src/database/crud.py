from datetime import date
from typing import List, Optional
from sqlalchemy.orm import Session

from .models import TaskORM, EventORM, WellnessGoalORM, PreferencesORM, PlanORM, PlanBlockORM


# Tasks

def create_task(db: Session, title: str, estimated_minutes: int, priority: int, due_date: date, course: Optional[str] = None, notes: Optional[str] = None) -> TaskORM:
    task = TaskORM(
        title=title,
        estimated_minutes=estimated_minutes,
        priority=priority,
        due_date=due_date,
        course=course,
        notes=notes,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get_task(db: Session, task_id: int) -> Optional[TaskORM]:
    return db.query(TaskORM).filter(TaskORM.id == task_id).first()


def get_all_tasks(db: Session) -> List[TaskORM]:
    return db.query(TaskORM).all()


def update_task(db: Session, task_id: int, **kwargs) -> Optional[TaskORM]:
    task = get_task(db, task_id)
    if not task:
        return None
    for key, value in kwargs.items():
        if hasattr(task, key) and value is not None:
            setattr(task, key, value)
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task_id: int) -> bool:
    task = get_task(db, task_id)
    if not task:
        return False
    db.delete(task)
    db.commit()
    return True


# Events

def create_event(db: Session, name: str, date: date, start_time, end_time,
                 category: Optional[str] = None) -> EventORM:
    event = EventORM(
        name=name,
        date=date,
        start_time=start_time,
        end_time=end_time,
        category=category,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def get_event(db: Session, event_id: int) -> Optional[EventORM]:
    return db.query(EventORM).filter(EventORM.id == event_id).first()


def get_all_events(db: Session) -> List[EventORM]:
    return db.query(EventORM).all()


def delete_event(db: Session, event_id: int) -> bool:
    event = get_event(db, event_id)
    if not event:
        return False
    db.delete(event)
    db.commit()
    return True


# WellnessGoal

def create_wellness_goal(db: Session, min_sleep_hours_per_day: float, workouts_per_week: int, meals_per_day: int,self_care_blocks_per_week: int) -> WellnessGoalORM:
    goal = WellnessGoalORM(
        min_sleep_hours_per_day=min_sleep_hours_per_day,
        workouts_per_week=workouts_per_week,
        meals_per_day=meals_per_day,
        self_care_blocks_per_week=self_care_blocks_per_week,
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


def get_latest_wellness_goal(db: Session) -> Optional[WellnessGoalORM]:
    return db.query(WellnessGoalORM).order_by(WellnessGoalORM.id.desc()).first()


# Preferences

def create_preferences(db: Session, earliest_start, latest_end, study_block_minutes: int, break_minutes: int) -> PreferencesORM:
    prefs = PreferencesORM(
        earliest_start=earliest_start,
        latest_end=latest_end,
        study_block_minutes=study_block_minutes,
        break_minutes=break_minutes,
    )
    db.add(prefs)
    db.commit()
    db.refresh(prefs)
    return prefs


def get_latest_preferences(db: Session) -> Optional[PreferencesORM]:
    return db.query(PreferencesORM).order_by(PreferencesORM.id.desc()).first()


# Plans

def create_plan(db: Session, week_start: date, weekly_balance_score: Optional[float], blocks: List[dict]) -> PlanORM:
    """
    Persist a generated plan. `blocks` is the list of block dicts from the engine,
    each with keys: day, start, end, category.
    """
    plan = PlanORM(
        created_at=date.today(),
        week_start=week_start,
        weekly_balance_score=weekly_balance_score,
    )
    db.add(plan)
    db.flush()  # get plan.id before adding blocks

    for block in blocks:
        db.add(PlanBlockORM(
            plan_id=plan.id,
            day=block["day"],
            start_time=block["start"],
            end_time=block["end"],
            category=block["category"],
        ))

    db.commit()
    db.refresh(plan)
    return plan


def get_plan(db: Session, plan_id: int) -> Optional[PlanORM]:
    return db.query(PlanORM).filter(PlanORM.id == plan_id).first()


def get_all_plans(db: Session) -> List[PlanORM]:
    return db.query(PlanORM).order_by(PlanORM.created_at.desc()).all()

# Users
def create_user(db: Session, email: str, hashed_password: str) -> "UserORM":
    from .models import UserORM
    user = UserORM(
        email=email,
        hashed_password=hashed_password,
        created_at=date.today(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_email(db: Session, email: str) -> Optional["UserORM"]:
    from .models import UserORM
    return db.query(UserORM).filter(UserORM.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> Optional["UserORM"]:
    from .models import UserORM
    return db.query(UserORM).filter(UserORM.id == user_id).first()