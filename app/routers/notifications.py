from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user
from app.models import Notification, User
from datetime import datetime
from app.schemas import TokenRequest

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.post("/token")
def save_fcm_token(
    data: TokenRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    print("🔥 RECEIVED TOKEN:", data.token)  # IMPORTANT

    current_user.fcm_token = data.token
    db.commit()

    return {"status": "token saved"}


@router.get("/my")
def get_my_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id)
        .filter(Notification.delivered == True)
        .order_by(Notification.created_at.desc())
        .all()
    )


@router.post("/test-sticky")
def test_sticky_notification(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.fcm_token:
         return {"error": "No FCM token found"}
    
    # Store in DB so it shows in web list
    notif = Notification(
        user_id=current_user.id,
        title="Test Sticky",
        body="This notification should be hard to clear.",
        notify_at=datetime.now(),
        delivered=True
    )
    db.add(notif)
    db.commit()

    from app.services.push import send_push_notification
    send_push_notification(
        fcm_token=current_user.fcm_token,
        title=notif.title,
        body=notif.body,
        sticky=True
    )
    return {"status": "sent", "id": notif.id}


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def clear_all_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db.query(Notification).filter(Notification.user_id == current_user.id).delete()
    db.commit()
    return None

@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notif = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.user_id == current_user.id
    ).first()
    
    if not notif:
         raise HTTPException(status_code=404, detail="Notification not found")
         
    db.delete(notif)
    db.commit()
    return None
