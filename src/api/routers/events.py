from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ...database.session import get_db
from ...database.crud import create_event, get_event, get_all_events, delete_event
from ..schemas import EventCreate, EventResponse

router = APIRouter(prefix="/events", tags=["events"])


@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create(payload: EventCreate, db: Session = Depends(get_db)) -> EventResponse:
    return create_event(
        db,
        name=payload.name,
        date=payload.date,
        start_time=payload.start_time,
        end_time=payload.end_time,
        category=payload.category,
    )


@router.get("/", response_model=List[EventResponse])
def list_all(db: Session = Depends(get_db)) -> List[EventResponse]:
    return get_all_events(db)


@router.get("/{event_id}", response_model=EventResponse)
def retrieve(event_id: int, db: Session = Depends(get_db)) -> EventResponse:
    event = get_event(db, event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(event_id: int, db: Session = Depends(get_db)) -> None:
    if not delete_event(db, event_id):
        raise HTTPException(status_code=404, detail="Event not found")