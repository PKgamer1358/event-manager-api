from app.database import engine, Base
from app.models import User, Event, Registration, Notification, EventMedia, Student
# Import all models to ensure they are registered with Base.metadata

def force_sync():
    print("\n" + "="*50)
    print("RECOVERY: Forcing Database Schema Sync")
    print("="*50)
    try:
        print("Attempting to create any missing tables using Base.metadata.create_all()...")
        Base.metadata.create_all(bind=engine)
        print("Sync command finished successfully.")
    except Exception as e:
        print(f"RECOVERY FAILED: {str(e)}")
    print("="*50 + "\n")

if __name__ == "__main__":
    force_sync()
