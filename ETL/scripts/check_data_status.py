"""
Check data loading status in PostgreSQL database.
Shows row counts for all tables and sample data.
"""

import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

def get_database_url():
    """Get DATABASE_URL from environment."""
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("❌ ERROR: DATABASE_URL environment variable not set")
        print("\nSet it with:")
        print('  $env:DATABASE_URL = "postgresql://etl_user:etl_password_123@localhost:5432/ETL_DB"')
        sys.exit(1)
    return db_url

def check_table_data(engine):
    """Check row counts and sample data for all tables."""
    print("\n" + "=" * 80)
    print("  DATABASE DATA STATUS")
    print("=" * 80)
    
    tables = [
        'dim_customers',
        'dim_products',
        'dim_sellers',
        'dim_geolocation',
        'dim_product_category_translation',
        'fact_orders',
        'fact_order_items',
        'fact_payments',
        'fact_reviews',
        'ingest_audit',
        'orders'
    ]
    
    with engine.connect() as conn:
        for table in tables:
            try:
                # Get row count
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                
                # Get column count
                col_result = conn.execute(text(f"""
                    SELECT COUNT(*) 
                    FROM information_schema.columns 
                    WHERE table_name = '{table}'
                """))
                col_count = col_result.scalar()
                
                status = "✅" if count > 0 else "⚠️ "
                print(f"\n{status} {table}")
                print(f"   Rows: {count:,}")
                print(f"   Columns: {col_count}")
                
                if count > 0:
                    # Show sample data
                    sample = pd.read_sql(text(f"SELECT * FROM {table} LIMIT 3"), conn)
                    print(f"   Sample columns: {', '.join(sample.columns.tolist()[:5])}")
                else:
                    print(f"   ⚠️  NO DATA - Table is empty!")
                    
            except Exception as e:
                print(f"\n❌ {table}")
                print(f"   Error: {str(e)}")

def check_staging_files():
    """Check if CSV files exist in staging."""
    print("\n" + "=" * 80)
    print("  STAGING CSV FILES")
    print("=" * 80 + "\n")
    
    staging_paths = [
        Path('data/staging'),
        Path('../brazilian dataset'),
        Path('brazilian dataset')
    ]
    
    for staging_path in staging_paths:
        if staging_path.exists():
            csv_files = list(staging_path.glob('*.csv'))
            if csv_files:
                print(f"📁 Found {len(csv_files)} CSV files in: {staging_path.absolute()}\n")
                for csv_file in csv_files:
                    size_mb = csv_file.stat().st_size / (1024 * 1024)
                    print(f"   • {csv_file.name:45} {size_mb:>8.2f} MB")
                return True
    
    print("⚠️  No CSV files found in staging folders")
    return False

def main():
    """Main execution function."""
    print("=" * 80)
    print("  PostgreSQL Data Loading Status Checker")
    print("=" * 80)
    
    # Get database connection
    db_url = get_database_url()
    print(f"\n📊 Database: {db_url.split('@')[-1] if '@' in db_url else 'localhost'}")
    
    # Create engine
    try:
        engine = create_engine(db_url)
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Database connection successful\n")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)
    
    # Check table data
    check_table_data(engine)
    
    # Check staging files
    check_staging_files()
    
    print("\n" + "=" * 80)
    print("  RECOMMENDATIONS")
    print("=" * 80 + "\n")
    
    print("If tables are empty, load data with:")
    print("  python scripts/load_brazilian_data.py")
    print("\nIf you see errors, check:")
    print("  1. CSV files exist in 'brazilian dataset' folder")
    print("  2. Tables were created: sql/add_missing_tables.sql")
    print("  3. User has permissions: GRANT ALL ON ALL TABLES TO etl_user")
    print("\n" + "=" * 80 + "\n")

if __name__ == '__main__':
    main()
