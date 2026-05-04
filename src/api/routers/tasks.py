from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...database.session import get_db
from ...database.crud import (
    create_task, get_task, get_all_tasks, update_task, delete_task
)
from ..schemas import TaskCreate, TaskUpdate, TaskResponse

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create(payload: TaskCreate, db: Session = Depends(get_db)) -> TaskResponse:
    return create_task(
        db,
        title=payload.title,
        estimated_minutes=payload.estimated_minutes,
        priority=payload.priority,
        due_date=payload.due_date,
        course=payload.course,
        notes=payload.notes,
    )


@router.get("/", response_model=List[TaskResponse])
def list_all(db: Session = Depends(get_db)) -> List[TaskResponse]:
    return get_all_tasks(db)


@router.get("/{task_id}", response_model=TaskResponse)
def retrieve(task_id: int, db: Session = Depends(get_db)) -> TaskResponse:
    task = get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
def update(task_id: int, payload: TaskUpdate,
           db: Session = Depends(get_db)) -> TaskResponse:
    task = update_task(db, task_id, **payload.model_dump(exclude_unset=True))
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(task_id: int, db: Session = Depends(get_db)) -> None:
    if not delete_task(db, task_id):
        raise HTTPException(status_code=404, detail="Task not found")