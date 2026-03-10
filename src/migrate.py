"""
Database migration script to add User Auth and Favorites
"""
import sys
import os
from sqlalchemy import text

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import engine
from src.models import Base

def migrate():
    print("🚀 Running database migrations...")
    
    # Create the new user table
    Base.metadata.create_all(bind=engine)
    print("✅ Created new tables (e.g. users) if they didn't exist")
    
    with engine.begin() as conn:
        print("🔧 Altering sessions table...")
        try:
            # We use Postgres syntax
            conn.execute(text("ALTER TABLE sessions ADD COLUMN user_id VARCHAR(36) REFERENCES users(id) ON DELETE CASCADE;"))
            print("✅ Added user_id to sessions")
        except Exception as e:
            if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                print("⚠️ user_id already exists on sessions")
            else:
                print(f"❌ Error adding user_id to sessions: {e}")
                
        print("🔧 Altering conversations table...")
        try:
            conn.execute(text("ALTER TABLE conversations ADD COLUMN is_favorite BOOLEAN NOT NULL DEFAULT FALSE;"))
            print("✅ Added is_favorite to conversations")
        except Exception as e:
            if "already exists" in str(e).lower() or "duplicate column" in str(e).lower():
                print("⚠️ is_favorite already exists on conversations")
            else:
                print(f"❌ Error adding is_favorite to conversations: {e}")
                
    print("🎉 Migrations complete!")

if __name__ == "__main__":
    migrate()
