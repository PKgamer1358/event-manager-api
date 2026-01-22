from sqlalchemy import create_engine, inspect, text
from app.config import settings
import sys

def check_tables():
    print("\n" + "="*50)
    print("DIAGNOSTIC: Checking Database Tables")
    print("="*50)
    
    try:
        # Create engine
        engine = create_engine(settings.DATABASE_URL)
        
        # Connect and check version
        with engine.connect() as connection:
            result = connection.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"Database Version: {version}")
            
            # Check current schema
            result = connection.execute(text("SELECT current_schema();"))
            schema = result.fetchone()[0]
            print(f"Current Schema: {schema}")

        # Inspect tables
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"Tables found in DB: {tables}")
        
        required_tables = ["users", "events", "notifications"]
        missing = [t for t in required_tables if t not in tables]
        
        if missing:
            print(f"CRITICAL ERROR: Missing tables: {missing}")
            print("Migrations might have failed or not committed.")
        else:
            print("SUCCESS: All required tables found.")
            
    except Exception as e:
        print(f"DIAGNOSTIC FAILED: {str(e)}")
        
    print("="*50 + "\n")

if __name__ == "__main__":
    check_tables()
