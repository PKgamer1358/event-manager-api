from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from app.core.firebase import send_fcm
from app.database import SessionLocal
from app.models import Notification
from datetime import datetime
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Notification
from app.services.push import send_push_notification  # adjust if needed
# scheduler = BackgroundScheduler()
# scheduler.start()

def store_web_notification(user_id: int, title: str, body: str):
    db = SessionLocal()
    try:
        notif = Notification(
            user_id=user_id,
            title=title,
            body=body,
            notify_at=datetime.utcnow() + timedelta(hours=5, minutes=30)
        )
        db.add(notif)
        db.commit()
    finally:
        db.close()

def schedule_notification(
    user_id: int,
    title: str,
    body: str,
    notify_at: datetime
):
    db: Session = SessionLocal()
    try:
        notif = Notification(
            user_id=user_id,
            title=title,
            body=body,
            notify_at=notify_at,
            delivered=False
        )
        db.add(notif)
        db.commit()
        # Optionally trigger scheduler if needed, but for now we rely on DB polling or external scheduler
    finally:
        db.close()
def send_notification(user, title, body):
    # 1. ALWAYS store in the database (so it shows in the "Notifications" tab)
    store_web_notification(user.id, title, body)

    # 2. If they have a phone connected, ALSO send a push
    if user.fcm_token:
        try:
            send_fcm(
                token=user.fcm_token,
                title=title,
                body=body
            )
        except Exception as e:
            print(f"Failed to send Push Notification: {e}")

def send_due_notifications():
    db: Session = SessionLocal()
    try:
        # 🕒 TIMEZONE FIX:
        # Server is likely UTC. DB timestamps are naive IST.
        # We must compare IST to IST.
        from datetime import timedelta
        server_now = datetime.utcnow()
        now_ist = server_now + timedelta(hours=5, minutes=30)

        notifications = (
            db.query(Notification)            .filter(
                Notification.notify_at <= now_ist,
                Notification.delivered == False
            )
            .all()
        )

        for n in notifications:
            if n.user and n.user.fcm_token:
                # 1-day reminder is sticky (cannot be swiped away)
                is_sticky = n.title.startswith("Upcoming Tomorrow")

                try:
                    send_push_notification(
                        fcm_token=n.user.fcm_token,
                        title=n.title,
                        body=n.body,
                        sticky=is_sticky
                    )
                except Exception as e:
                    print(f"Error sending push notification to user {n.user_id}: {e}")

            n.delivered = True

        db.commit()

    finally:
        db.close()
