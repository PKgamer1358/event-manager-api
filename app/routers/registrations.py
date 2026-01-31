from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session, joinedload
from typing import List
from io import BytesIO
from openpyxl import Workbook
from fastapi.responses import StreamingResponse
from app.database import get_db
from app.models import User, Event, Registration
from app.routers.events import get_event
from app.schemas import RegistrationResponse, RegistrationWithUser, MessageResponse, RegistrationWithEvent
from app.dependencies import get_current_user, get_current_admin_user
from app.utils.permissions import can_manage_event
from datetime import datetime, timedelta
from app.services.notifications import schedule_notification, send_notification
from app.services.email import send_registration_confirmation

# IST Offset
IST_OFFSET = timedelta(hours=5, minutes=30)

router = APIRouter(prefix="/registrations", tags=["Registrations"])


@router.post(
    "/events/{event_id}/register",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED
)
def register_for_event(
    event_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1️⃣ Check if event exists
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    # 1.5 Check if event is in the past
    now_ist = datetime.utcnow() + IST_OFFSET
    if event.start_time < now_ist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot register for a past event"
        )

    # 2️⃣ Check if already registered for this event
    existing_registration = db.query(Registration).filter(
        Registration.user_id == current_user.id,
        Registration.event_id == event_id
    ).first()

    if existing_registration:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already registered for this event"
        )

    # 3️⃣ 🔥 CHECK OVERLAPPING EVENTS (THIS IS THE IMPORTANT PART)
    # 3️⃣ 🔥 CHECK OVERLAPPING EVENTS
    overlapping_events = []
    if event.end_time:
        overlapping_events = (
            db.query(Event)
            .join(Registration, Registration.event_id == Event.id)
            .filter(Registration.user_id == current_user.id)
            .filter(
                Event.start_time < event.end_time,
                Event.end_time > event.start_time
            )
            .all()
        )

    if overlapping_events:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already registered for another event during this time"
        )

    # 4️⃣ Check capacity
    if event.is_full:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Event is full"
        )

    # 5️⃣ Create registration
    new_registration = Registration(
        user_id=current_user.id,
        event_id=event_id
    )

    db.add(new_registration)
    db.commit()
    db.refresh(new_registration)

    # 5.5️⃣ Send Immediate Confirmation
    try:
        send_notification(
            user=current_user,
            title="Registration Confirmed",
            body=f"You have successfully registered for {event.title}!"
        )
    except Exception as e:
        print(f"Error sending immediate notification: {e}")

    # 5.6️⃣ Send Email Confirmation
    background_tasks.add_task(send_registration_confirmation, current_user, event)

    # 6️⃣ Schedule reminders
    event_start = event.start_time
    one_day_before = event_start - timedelta(days=1)
    three_hours_before = event_start - timedelta(hours=3)

    # 1 Day Before (Sticky)
    if one_day_before > now_ist:
        schedule_notification(
            user_id=current_user.id,
            title=f"Upcoming Tomorrow: {event.title}",
            body=f"Don't forget! {event.title} is tomorrow at {event.start_time.strftime('%I:%M %p')}",
            notify_at=one_day_before
        )

    # 3 Hours Before (Standard)
    if three_hours_before > now_ist:
        schedule_notification(
            user_id=current_user.id,
            title=f"Starting Soon: {event.title}",
            body=f"Get ready! {event.title} starts soon at {event.start_time.strftime('%I:%M %p')}",
            notify_at=three_hours_before
        )

    return MessageResponse(
        message="Successfully registered for event",
        detail=f"Registration ID: {new_registration.id}"
    )




@router.delete("/events/{event_id}/register", response_model=MessageResponse)
def unregister_from_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Unregister current user from an event
    """
    # Find registration
    # Find registration
    registration = (
        db.query(Registration)
        .options(joinedload(Registration.event))
        .filter(
            Registration.user_id == current_user.id,
            Registration.event_id == event_id
        )
        .first()
    )
    
    if not registration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registration not found"
        )
    
    # Check 5-day rule
    event = registration.event
    now_ist = datetime.utcnow() + IST_OFFSET
    if event.start_time - now_ist <= timedelta(days=3):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot unregister within 3 days of the event start date"
        )

    db.delete(registration)
    db.commit()
    
    return MessageResponse(
        message="Successfully unregistered from event",
        detail=f"Event ID: {event_id}"
    )


@router.get("/events/{event_id}/registrations", response_model=List[RegistrationWithUser])
def get_event_registrations(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all registrations for an event (admin or event creator only)
    """
    # Check if event exists
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Check permission (admin or event creator)
    if not current_user.is_admin and event.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view registrations for this event"
        )
    
    # Get registrations
    registrations = db.query(Registration).filter(
        Registration.event_id == event_id
    ).all()
    
    return registrations


@router.get("/my-registrations", response_model=List[RegistrationWithEvent])
def get_my_registrations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Registration)
        .options(joinedload(Registration.event))  # ← THE FIX
        .filter(Registration.user_id == current_user.id)
        .all()
    )

@router.get("/events/{event_id}/export")
def export_event_registrations(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Fetch event
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )

    # ✅ FIXED PERMISSION: admin OR super admin
    if not (current_user.is_admin or current_user.is_super_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to export registrations"
        )

    registrations = (
        db.query(Registration)
        .options(
            joinedload(Registration.user)
            .joinedload(User.student_profile)
        )
        .filter(Registration.event_id == event_id)
        .all()
    )

    wb = Workbook()
    ws = wb.active
    ws.title = "Registrations"

    # Header
    ws.append([
        "S.No",
        "USN",
        "Full Name",
        "Email",
        "Year",
        "Branch",
        "Registered On"
    ])

    ws.freeze_panes = "A2"

    from openpyxl.styles import Font
    for cell in ws[1]:
        cell.font = Font(bold=True)

    ws.column_dimensions["A"].width = 8
    ws.column_dimensions["B"].width = 18
    ws.column_dimensions["C"].width = 25
    ws.column_dimensions["D"].width = 30
    ws.column_dimensions["E"].width = 10
    ws.column_dimensions["F"].width = 20
    ws.column_dimensions["G"].width = 22

    for index, reg in enumerate(registrations, start=1):
        user = reg.user
        student = user.student_profile

        ws.append([
            index,
            student.roll_number if student else "",
            f"{user.first_name} {user.last_name}",
            user.email,
            student.year_of_study if student else "",
            student.branch if student else "",
            reg.registered_at.strftime("%Y-%m-%d %H:%M"),
        ])

    file_stream = BytesIO()
    wb.save(file_stream)
    file_stream.seek(0)

    return StreamingResponse(
        file_stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=event_{event_id}_registrations.xlsx"
        },
    )

@router.get("/debug-time/{event_id}")
def debug_event_timing(
    event_id: int,
    db: Session = Depends(get_db),
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        return {"error": "Event not found"}
        
    now_ist = datetime.utcnow() + IST_OFFSET
    one_day = event.start_time - timedelta(days=1)
    three_hours = event.start_time - timedelta(hours=3)
    
    return {
        "server_now_utc": datetime.utcnow(),
        "server_now_ist": now_ist,
        "event_start": event.start_time,
        "one_day_before": one_day,
        "one_day_is_future": one_day > now_ist,
        "three_hours_before": three_hours,
        "three_hours_is_future": three_hours > now_ist,
        "delta_hours": (three_hours - one_day).total_seconds() / 3600
    }

