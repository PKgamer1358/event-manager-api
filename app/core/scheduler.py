from apscheduler.schedulers.background import BackgroundScheduler
from app.services.notifications import send_due_notifications

scheduler = BackgroundScheduler()

def start_scheduler():
    scheduler.add_job(
        send_due_notifications,
        "interval",
        minutes=1,   # checks every minute
    )
    scheduler.start()
