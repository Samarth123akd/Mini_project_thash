#!/usr/bin/env python3
"""
Update database schema to include all Brazilian dataset tables.

This script adds the missing tables for the complete Brazilian dataset:
- dim_sellers
- dim_geolocation
- dim_product_category_translation
- fact_reviews

Usage:
    $env:DATABASE_URL = "postgresql://user:pass@localhost:5432/etl_db"
    python scripts/update_schema.py
"""

import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text

def get_database_url():
    """Get DATABASE_URL from environment."""
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("❌ ERROR: DATABASE_URL environment variable not set")
        print("\nSet it with:")
        print('  $env:DATABASE_URL = "postgresql://user:pass@localhost:5432/etl_db"')
        sys.exit(1)
    return db_url

def check_table_exists(conn, table_name):
    """Check if a table already exists."""
    result = conn.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = :table_name
        )
    """), {'table_name': table_name})
    return result.scalar()

def create_missing_tables(engine):
    """Create any missing tables in the database."""
    print("\n🔧 Checking and creating missing tables...\n")
    
    with engine.connect() as conn:
        # Check and create dim_sellers
        if not check_table_exists(conn, 'dim_sellers'):
            print("   Creating dim_sellers...")
            conn.execute(text("""
                CREATE TABLE dim_sellers (
                    seller_id TEXT PRIMARY KEY,
                    seller_zip_code_prefix TEXT,
                    seller_city TEXT,
                    seller_state TEXT,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """))
            conn.execute(text("CREATE INDEX idx_sellers_state ON dim_sellers(seller_state)"))
            conn.execute(text("CREATE INDEX idx_sellers_city ON dim_sellers(seller_city)"))
            print("   ✅ dim_sellers created")
        else:
            print("   ✓ dim_sellers already exists")
        
        # Check and create dim_geolocation
        if not check_table_exists(conn, 'dim_geolocation'):
            print("   Creating dim_geolocation...")
            conn.execute(text("""
                CREATE TABLE dim_geolocation (
                    geolocation_id SERIAL PRIMARY KEY,
                    geolocation_zip_code_prefix TEXT,
                    geolocation_lat DOUBLE PRECISION,
                    geolocation_lng DOUBLE PRECISION,
                    geolocation_city TEXT,
                    geolocation_state TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """))
            conn.execute(text("CREATE INDEX idx_geo_zip ON dim_geolocation(geolocation_zip_code_prefix)"))
            conn.execute(text("CREATE INDEX idx_geo_state ON dim_geolocation(geolocation_state)"))
            conn.execute(text("CREATE INDEX idx_geo_coords ON dim_geolocation(geolocation_lat, geolocation_lng)"))
            print("   ✅ dim_geolocation created")
        else:
            print("   ✓ dim_geolocation already exists")
        
        # Check and create dim_product_category_translation
        if not check_table_exists(conn, 'dim_product_category_translation'):
            print("   Creating dim_product_category_translation...")
            conn.execute(text("""
                CREATE TABLE dim_product_category_translation (
                    product_category_name TEXT PRIMARY KEY,
                    product_category_name_english TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """))
            print("   ✅ dim_product_category_translation created")
        else:
            print("   ✓ dim_product_category_translation already exists")
        
        # Check and create fact_reviews
        if not check_table_exists(conn, 'fact_reviews'):
            print("   Creating fact_reviews...")
            conn.execute(text("""
                CREATE TABLE fact_reviews (
                    review_id TEXT PRIMARY KEY,
                    order_id TEXT REFERENCES fact_orders(order_id),
                    review_score INTEGER,
                    review_comment_title TEXT,
                    review_comment_message TEXT,
                    review_creation_date TIMESTAMP WITH TIME ZONE,
                    review_answer_timestamp TIMESTAMP WITH TIME ZONE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                )
            """))
            conn.execute(text("CREATE INDEX idx_reviews_order ON fact_reviews(order_id)"))
            conn.execute(text("CREATE INDEX idx_reviews_score ON fact_reviews(review_score)"))
            conn.execute(text("CREATE INDEX idx_reviews_date ON fact_reviews(review_creation_date)"))
            print("   ✅ fact_reviews created")
        else:
            print("   ✓ fact_reviews already exists")
        
        conn.commit()

def list_all_tables(engine):
    """List all tables in the database."""
    print("\n📊 Current database tables:\n")
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT table_name, 
                   pg_size_pretty(pg_total_relation_size(quote_ident(table_name)::regclass)) as size
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """))
        
        for row in result:
            print(f"   {row[0]:40} {row[1]:>15}")

def main():
    """Main execution function."""
    print("=" * 60)
    print("  Database Schema Update for Brazilian Dataset")
    print("=" * 60)
    
    # Get database connection
    db_url = get_database_url()
    print(f"\n📊 Database: {db_url.split('@')[-1] if '@' in db_url else 'localhost'}")
    
    # Create engine
    try:
        engine = create_engine(db_url)
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)
    
    try:
        # Create missing tables
        create_missing_tables(engine)
        
        # List all tables
        list_all_tables(engine)
        
        print("\n" + "=" * 60)
        print("  ✅ SUCCESS! Schema updated")
        print("=" * 60)
        print("\nNext steps:")
        print("  1. Load data: python scripts/load_brazilian_data.py")
        print("  2. Verify data: python scripts/view_data.py")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
