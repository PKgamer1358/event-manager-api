from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Event, Registration, Student, User
from app.dependencies import get_current_admin_user
from sqlalchemy import func
from datetime import date

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/event/{event_id}")
def event_analytics(
    event_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin_user),
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    registered_count = (
        db.query(Registration)
        .filter(Registration.event_id == event_id)
        .count()
    )

    remaining = max(event.capacity - registered_count, 0)

    return {
        "labels": ["Registered", "Remaining"],
        "values": [registered_count, remaining],
        "capacity": event.capacity,
    }


@router.get("/event/{event_id}/registrations-over-time")
def registrations_over_time(
    event_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin_user),
):
    results = (
        db.query(
            func.date(Registration.registered_at).label("day"),
            func.count(Registration.id).label("count"),
        )
        .filter(Registration.event_id == event_id)
        .group_by(func.date(Registration.registered_at))
        .order_by(func.date(Registration.registered_at))
        .all()
    )

    return [
        {"date": r.day.isoformat(), "count": r.count}
        for r in results
    ]

@router.get("/event/{event_id}/registrations-by-year")
def registrations_by_year(
    event_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin_user),
):
    results = (
        db.query(
            Student.year_of_study,
            func.count(Registration.id),
        )
        .join(User, User.id == Registration.user_id)
        .join(Student, Student.user_id == User.id)
        .filter(Registration.event_id == event_id)
        .group_by(Student.year_of_study)
        .all()
    )

    return [
        {"year": year or "Unknown", "count": count}
        for year, count in results
    ]

