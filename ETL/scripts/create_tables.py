#!/usr/bin/env python3
"""Create database tables from schema.sql"""

from sqlalchemy import create_engine, text
import sys
import os

# Prefer environment variable; fallback remains for local dev
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://etl_user:etl_password_123@localhost:5432/etl_db",
)

def create_tables():
    """Create all tables from schema.sql"""
    try:
        engine = create_engine(DATABASE_URL)
        
        # Read schema file
        with open('sql/schema.sql', 'r') as f:
            schema_sql = f.read()
        
        # Execute schema
        with engine.connect() as conn:
            # Ensure dedicated schema exists and is owned by etl_user
            conn.execute(text("CREATE SCHEMA IF NOT EXISTS etl AUTHORIZATION etl_user"))
            # Use the etl schema for this session so unqualified CREATEs land in etl
            conn.execute(text("SET search_path TO etl, public"))

            # Split by semicolon and execute each statement
            statements = [s.strip() for s in schema_sql.split(';') if s.strip()]
            for statement in statements:
                conn.execute(text(statement))
            conn.commit()
        
        print("✅ Tables created successfully!")
        
        # Verify tables
        with engine.connect() as conn:
            conn.execute(text("SET search_path TO etl, public"))
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'etl'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            print(f"\n📋 Created {len(tables)} tables:")
            for table in tables:
                print(f"  - {table}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

if __name__ == "__main__":
    success = create_tables()
    sys.exit(0 if success else 1)
