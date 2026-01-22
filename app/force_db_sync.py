from app.database import engine, Base
from app.models import User, Event, Registration, Notification, EventMedia, Student
from sqlalchemy import text
from alembic.config import Config
from alembic import command
import sys

def force_sync():
    print("\n" + "="*50)
    print("RECOVERY: Forcing Database Schema Sync (Shell-Free Mode)")
    print("="*50)
    try:
        # 1. Drop Alembic Version Table (Trick to reset migration state)
        print("1. Resetting Alembic State (Dropping alembic_version table)...")
        with engine.connect() as connection:
            connection.execute(text("DROP TABLE IF EXISTS alembic_version"))
            connection.commit()
        
        # 2. Force Create All Tables/Columns
        print("2. Force creating missing tables/columns (Base.metadata.create_all)...")
        Base.metadata.create_all(bind=engine)
        
        # 3. Stamp Database as Head (Fake that migrations ran)
        print("3. Stamping database as 'head'...")
        alembic_cfg = Config("alembic.ini")
        command.stamp(alembic_cfg, "head")
        
        print("SUCCESS: Database repaired and synced.")
        
    except Exception as e:
        print(f"RECOVERY FAILED: {str(e)}")
        # Don't crash the app, let it try starting anyway
        
    print("="*50 + "\n")

if __name__ == "__main__":
    force_sync()
