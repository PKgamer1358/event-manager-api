from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile
import shutil
import os
from datetime import datetime
from app.config import settings
from sqlalchemy.orm import Session
from typing import List,Optional

from app.database import get_db
from app.models import User, Event, EventMedia
from app.schemas import EventCreate, EventResponse, MessageResponse, EventUpdate, EventMediaResponse
from app.dependencies import get_current_user, get_current_admin_user
from app.utils.permissions import can_manage_event
from fastapi.responses import StreamingResponse
import io
import cloudinary
import cloudinary.uploader
from app.services.media import upload_to_cloudinary


router = APIRouter(prefix="/events", tags=["Events"])

def normalize_club(club: str | None):
    if not club:
        return None
    return club.strip().title()
def normalize_url(u):
    return u.strip() if u else None
def normalize_text(s: str | None):
    return s.strip().title() if s else None

def can_manage_event(user: User, event: Event) -> bool:
    print(
        "CHECK:",
        "user:", user.id,
        "admin:", user.is_admin,
        "super:", user.is_super_admin,
        "event.created_by:", event.created_by,
    )
    return (
        user.is_super_admin or
        (user.is_admin and event.created_by == user.id)
    )


@router.post("", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def create_event(
    event_data: EventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Create a new event (admin only)
    """
    # Validate end_time if provided
    if event_data.end_time and event_data.end_time <= event_data.start_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End time must be after start time"
        )
    
    # Create event
    new_event = Event(
        title=event_data.title,
        description=event_data.description,
        category=event_data.category,   # ✅ REQUIRED
        club=normalize_club(event_data.club),        venue=event_data.venue,
        start_time=event_data.start_time,
        end_time=event_data.end_time,
        capacity=event_data.capacity,
        created_by=current_user.id,
        image_url=event_data.image_url,
        
    )
    
    db.add(new_event)
    db.commit()
    db.refresh(new_event)
    
    return MessageResponse(
        message="Event created successfully",
        detail=f"Event ID: {new_event.id}"
    )


@router.get("", response_model=list[EventResponse])
def list_events(
    category: Optional[str] = Query(None),
    club: Optional[str] = Query(None),
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    query = db.query(Event)

    if category:
        query = query.filter(Event.category == category)

    if club:
        query = query.filter(Event.club == club)

    from datetime import datetime, timedelta
    
    # 🕒 TIMEZONE FIX: 
    # The server (Render/Vercel) likely runs in UTC.
    # The database stores timestamps as "naive" (no timezone info), but users input them as local time (IST).
    # So a user inputting "2:00 PM" is stored as "14:00".
    # But "now" on the server is UTC (e.g. "08:30" when it is 14:00 in India).
    # So "14:00" > "08:30", making the event look like it's in the future.
    # To fix this, we need to compare the "stored time" with "server time converted to IST".
    
    # Approx check for India (UTC+5:30)
    # If we add 5h 30m to server UTC time, we get approx IST time.
    server_now = datetime.utcnow()
    now_ist = server_now + timedelta(hours=5, minutes=30)
    
    # Use adjusted time for filtering
    # 1. Upcoming events
    upcoming_query = query.filter(Event.start_time >= now_ist).order_by(Event.start_time.asc())
    
    # 2. Past events
    past_query = query.filter(Event.start_time < now_ist).order_by(Event.start_time.desc())

    # Combine results
    # Note: Pagination (skip/limit) logic becomes complex with split queries. 
    # For now, we'll fetch them and slice in python or apply limit to the combined set if feasible.
    # Given the user request for "Open on top", proper pagination requires combining counts.
    # To keep it simple and functional for typical event volume:
    
    upcoming_events = upcoming_query.all()
    past_events = past_query.all()
    
    all_events = upcoming_events + past_events
    
    # Manual pagination
    start = skip
    end = skip + limit
    return all_events[start:end]


@router.get("/{event_id}", response_model=EventResponse)
def get_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific event by ID
    """
    event = db.query(Event).filter(Event.id == event_id).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    return event


@router.delete("/{event_id}", response_model=MessageResponse)
def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)

):
    """
    Delete an event (admin only)
    """
    event = db.query(Event).filter(Event.id == event_id).first()
    
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    if not can_manage_event(current_user, event):
      raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You are not allowed to delete this event"
      )

    db.delete(event)
    db.commit()
    
    return MessageResponse(
        message="Event deleted successfully",
        detail=f"Event ID: {event_id}"
    )


@router.put("/{event_id}", response_model=MessageResponse)
def update_event(
    event_id: int,
    event_data: EventUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing event (admin only)
    """
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    if not can_manage_event(current_user, event):
     raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You are not allowed to edit this event"
    )
    # Determine effective start/end times for validation
    new_start = event_data.start_time if event_data.start_time is not None else event.start_time
    new_end = event_data.end_time if event_data.end_time is not None else event.end_time
    if new_end is not None and new_start is not None and new_end <= new_start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End time must be after start time"
        )

    # Update fields when provided
    if event_data.title is not None:
        event.title = event_data.title
    if event_data.description is not None:
        event.description = event_data.description
    if event_data.venue is not None:
        event.venue = event_data.venue
    if event_data.start_time is not None:
        event.start_time = event_data.start_time
    if event_data.end_time is not None:
        event.end_time = event_data.end_time
    if event_data.capacity is not None:
        event.capacity = event_data.capacity

    db.commit()
    db.refresh(event)

    return MessageResponse(
        message="Event updated successfully",
        detail=f"Event ID: {event.id}"
    )


@router.post("/{event_id}/cover-image", response_model=MessageResponse)
async def upload_cover_image(
    event_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Upload cover image for an event (admin only).
    Replaces existing cover image if any.
    """
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Upload to Cloudinary
    try:
        upload_result = upload_to_cloudinary(
            file.file, 
            folder=f"events/event_{event_id}/cover",
            resource_type="image"
        )
        
        # Get secure URL
        file_url = upload_result.get("secure_url")
        
        # Update event
        event.image_url = file_url
        db.commit()
        
        return MessageResponse(
            message="Cover image uploaded successfully",
            detail=f"Image URL: {file_url}"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Cover upload error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cover upload failed: {str(e)}"
        )


@router.post("/{event_id}/upload", response_model=MessageResponse)
async def upload_event_media(
    event_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Upload media for an event (admin only)
    """
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # Configure Cloudinary
    cloudinary.config( 
        cloud_name = settings.CLOUDINARY_CLOUD_NAME, 
        api_key = settings.CLOUDINARY_API_KEY, 
        api_secret = settings.CLOUDINARY_API_SECRET 
    )

    # Validate file type
    content_type = file.content_type
    file_type = "document"
    if content_type and content_type.startswith("image/"):
        file_type = "image"
    elif content_type == "application/pdf":
        file_type = "pdf"

    # Upload to Cloudinary
    try:
        # folder="events/event_{event_id}" organizes files in Cloudinary
        upload_result = upload_to_cloudinary(
            file.file, 
            folder=f"events/event_{event_id}",
            resource_type="auto"
        )
        
        # Get secure URL
        file_url = upload_result.get("secure_url")
        
        media = EventMedia(
            event_id=event_id,
            file_url=file_url,
            file_type=file_type
        )
        
        db.add(media)
        db.commit()
        db.refresh(media)
        
        return MessageResponse(
            message="File uploaded successfully",
            detail=f"Media ID: {media.id}"
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Cloudinary upload error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image upload failed: {str(e)}"
        )


@router.get("/{event_id}/media", response_model=List[EventMediaResponse])
def get_event_media(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all media for an event
    """
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
        
    media_files = db.query(EventMedia).filter(EventMedia.event_id == event_id).all()
    return media_files


@router.delete("/{event_id}/media/{media_id}", response_model=MessageResponse)
def delete_event_media(
    event_id: int,
    media_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """
    Delete specific media from an event
    """
    # 1. Get Event and check permissions
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Event not found"
        )
    
    # 2. Check if user can manage this event
    if not can_manage_event(current_user, event):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to manage this event's media"
        )

    # 3. Get Media record
    media = db.query(EventMedia).filter(EventMedia.id == media_id, EventMedia.event_id == event_id).first()
    if not media:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Media file not found"
        )

    # 4. Remove file from Cloudinary
    if media.file_url:
        try:
            # Extract public_id from URL
            # Example: https://res.cloudinary.com/demo/image/upload/v1570979139/events/event_1/my_image.jpg
            # Public ID: events/event_1/my_image
            
            # Simple extraction strategy:
            # Split by '/' and take parts after 'upload/' (plus versioning handling if needed)
            # Cloudinary usually returns public_id in upload response, but if we don't store it, we must extract.
            # A safer way if possible is to store public_id in DB. 
            # For now, let's try to parse or just leave it as orphan if parsing fails (fallback).
            
            # Better strategy: Let's assume standard Cloudinary URL structure
            parts = media.file_url.split("/")
            # Find the 'upload' segment index
            try:
                upload_idx = parts.index("upload")
                # public_id starts after version (v12345) which is usually after upload
                # But sometimes version is omitted.
                # simpler: join from folder 'events' onwards and remove extension
                
                # We stored with folder=f"events/event_{event_id}"
                # So we look for that.
                
                # Find index of 'events'
                events_idx = parts.index("events")
                # Join from there to end
                public_id_with_ext = "/".join(parts[events_idx:])
                # Remove extension
                public_id = os.path.splitext(public_id_with_ext)[0]
                
                # Check resource type based on file_type
                # Cloudinary delete defaults to image. For PDFs/docs (raw), we might need to specify.
                # However, we used resource_type="auto" which might upload as image or raw.
                # Map our file_type to cloudinary resource_type
                res_type = "image"
                if media.file_type == "pdf" or media.file_type == "document":
                    # Check if it was uploaded as raw or image (PDFs can be both)
                    # For simplicity, try 'image' first, then 'raw' if needed? 
                    # Or just try to destroy.
                    pass # Default is image.
                
                # Important: "raw" files need resource_type="raw" in destroy
                # "image" and "video" are distinct.
                
                # For this implementation, we'll try to delete. 
                # If it fails, we log it.
                
                cloudinary.config( 
                    cloud_name = settings.CLOUDINARY_CLOUD_NAME, 
                    api_key = settings.CLOUDINARY_API_KEY, 
                    api_secret = settings.CLOUDINARY_API_SECRET 
                )
                
                cloudinary.uploader.destroy(public_id)
                # We might also need to try resource_type="raw" if it was a generic file
                cloudinary.uploader.destroy(public_id, resource_type="raw")
                
            except ValueError:
                print(f"Could not parse Cloudinary URL for deletion: {media.file_url}")

        except Exception as e:
            print(f"Error deleting file from Cloudinary: {e}")

    # 5. Delete DB record
    db.delete(media)
    db.commit()

    return MessageResponse(
        message="Media deleted successfully",
        detail=f"Media ID: {media_id}"
    )


# --- AI INSIGHTS ---

from pydantic import BaseModel

class InsightEvent(BaseModel):
    id: int
    title: str
    date: str

class InsightsResponse(BaseModel):
    demand_level: str  # "High", "Medium", "Low"
    top_demographics: List[str]  # e.g., "Computer Science - 3rd Year"
    similar_events: List[InsightEvent]

@router.get("/{event_id}/insights", response_model=InsightsResponse)
def get_event_insights(
    event_id: int,
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user) # Optional: open to public or restricted? Let's keep public for now or require auth if preferred.
):
    """
    Get 'AI' generated insights for an event based on heuristics.
    """
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # 1. Demand Level Logic
    # Simple velocity: regs / days_since_creation (or just total regs vs capacity ratio)
    demand = "Low"
    if event.capacity and event.capacity > 0:
        ratio = event.registered_count / event.capacity
        if ratio >= 0.8:
            demand = "Very High"
        elif ratio >= 0.5:
            demand = "High"
        elif ratio >= 0.2:
            demand = "Medium"
    else:
        # If no capacity, rely on raw count
        if event.registered_count > 50:
            demand = "High"
        elif event.registered_count > 10:
            demand = "Medium"

    # 2. Demographic Logic
    # Group registrations by Student branch/year
    # We need to join Registration -> User -> Student
    from sqlalchemy import func
    from app.models import Registration, Student
    
    # Simple Query: Top 2 branches
    top_branches = (
        db.query(Student.branch, func.count(Student.id))
        .join(User, User.id == Student.user_id)
        .join(Registration, Registration.user_id == User.id)
        .filter(Registration.event_id == event_id)
        .group_by(Student.branch)
        .order_by(func.count(Student.id).desc())
        .limit(2)
        .all()
    )
    
    top_demographics = []
    for branch, count in top_branches:
        if branch and count > 1: # Threshold to show
            top_demographics.append(f"{branch}")
            
    # If not enough branch info, maybe Year of Study?
    if not top_demographics:
        top_years = (
            db.query(Student.year_of_study, func.count(Student.id))
            .join(User, User.id == Student.user_id)
            .join(Registration, Registration.user_id == User.id)
            .filter(Registration.event_id == event_id)
            .group_by(Student.year_of_study)
            .order_by(func.count(Student.id).desc())
            .limit(1)
            .all()
        )
        for year, count in top_years:
            if year:
                top_demographics.append(f"Year {year} Students")

    # 3. Similar Events Logic
    # Same category, excluding self
    similar = []
    similar_db = db.query(Event).filter(
        Event.category == event.category, 
        Event.id != event.id,
        Event.start_time >= datetime.now() # Only future
    ).limit(3).all()
    
    for s in similar_db:
        similar.append(InsightEvent(
            id=s.id,
            title=s.title,
            date=s.start_time.strftime("%Y-%m-%d")
        ))

    return InsightsResponse(
        demand_level=demand,
        top_demographics=top_demographics,
        similar_events=similar
    )

# --- GLOBAL INSIGHTS ---

class GlobalInsightsResponse(BaseModel):
    # User fields
    trending_events: Optional[List[InsightEvent]] = []
    total_events_this_week: Optional[int] = 0
    total_registrations_today: Optional[int] = 0
    
    # Admin fields
    pending_users_count: Optional[int] = 0 # Deprecated/Optional
    at_risk_events_count: Optional[int] = 0 # Deprecated/Optional
    total_users_count: Optional[int] = 0 # Use as base user stat if needed
    
    # New Admin fields
    total_events_active: Optional[int] = 0
    total_events_past: Optional[int] = 0
    total_registrations_all_time: Optional[int] = 0
    total_registrations_this_week: Optional[int] = 0
    
    # Most Popular Event
    most_popular_event_title: Optional[str] = None
    most_popular_event_id: Optional[int] = None
    most_popular_event_count: Optional[int] = 0

from app.dependencies import get_current_user, get_current_admin_user, get_optional_current_user

@router.get("/insights/global", response_model=GlobalInsightsResponse)
def get_global_insights(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user) # Optional auth
):
    """
    Get global insights for the home page.
    Returns different data for Admin vs Student.
    """
    now = datetime.now()
    
    is_admin = current_user and current_user.is_admin

    if is_admin:
        # --- ADMIN INSIGHTS ---
        from app.models import User, Registration
        from datetime import timedelta
        from sqlalchemy import func
        
        last_week = now - timedelta(days=7)
        
        # 1. Total Events (Active vs Past)
        active_events = db.query(Event).filter(Event.start_time >= now).count()
        past_events = db.query(Event).filter(Event.start_time < now).count()
        
        # 2. Total Registrations (All time or This week)
        total_regs = db.query(Registration).count()
        new_regs = db.query(Registration).filter(Registration.registered_at >= last_week).count()
        
        # 3. Most Popular Event (Open / Upcoming)
        most_pop = (
            db.query(Event.title, Event.id, func.count(Registration.id))
            .join(Registration)
            .filter(Event.start_time >= now)
            .group_by(Event.id)
            .order_by(func.count(Registration.id).desc())
            .first()
        )
        
        pop_title = most_pop[0] if most_pop else None
        pop_id = most_pop[1] if most_pop else None
        pop_count = most_pop[2] if most_pop else 0
        
        return GlobalInsightsResponse(
            total_events_active=active_events,
            total_events_past=past_events,
            total_registrations_all_time=total_regs,
            total_registrations_this_week=new_regs,
            most_popular_event_title=pop_title,
            most_popular_event_id=pop_id,
            most_popular_event_count=pop_count
        )

    else:
        # --- STUDENT INSIGHTS (Existing) ---
    
        # 1. Trending Events
        trending_db = (
            db.query(Event)
            .filter(Event.start_time >= now)
            .all()
        )
        def fill_percentage(e):
            if not e.capacity: return 0
            return (len(e.registrations) / e.capacity)

        trending_db.sort(key=fill_percentage, reverse=True)
        trending_top_3 = trending_db[:3]
        
        trending = []
        for e in trending_top_3:
            trending.append(InsightEvent(
                id=e.id, 
                title=e.title, 
                date=e.start_time.strftime("%Y-%m-%d")
            ))
            
        # 2. Stats
        from datetime import timedelta
        start_of_week = now - timedelta(days=now.weekday())
        end_of_week = start_of_week + timedelta(days=7)
        
        events_this_week = db.query(Event).filter(
            Event.start_time >= start_of_week,
            Event.start_time < end_of_week
        ).count()
        
        from app.models import Registration
        start_of_day = datetime(now.year, now.month, now.day)
        regs_today = db.query(Registration).filter(
            Registration.registered_at >= start_of_day
        ).count()

        return GlobalInsightsResponse(
            trending_events=trending,
            total_events_this_week=events_this_week,
            total_registrations_today=regs_today
        )
