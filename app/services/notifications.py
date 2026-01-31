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

def store_web_notification(user_id: int, title: str, body: str, delivered: bool = False):
    db = SessionLocal()
    try:
        notif = Notification(
            user_id=user_id,
            title=title,
            body=body,
            notify_at=datetime.utcnow(),
            delivered=delivered
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
    # Mark as delivered since we are sending it immediately below
    store_web_notification(user.id, title, body, delivered=True)

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
        # We store notify_at in UTC (converted before saving).
        # So we compare against server UTC time.
        server_now = datetime.utcnow()

        notifications = (
            db.query(Notification)            .filter(
                Notification.notify_at <= server_now,
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
