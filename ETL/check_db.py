import os
from sqlalchemy import create_engine, text

os.environ['DATABASE_URL'] = "postgresql://postgres:Sam12kumar%40@localhost:5432/ETL_DB"
engine = create_engine(os.environ['DATABASE_URL'])

print("🔍 Checking Database Connection and Tables\n")
print("=" * 60)

with engine.connect() as conn:
    # Check tables
    result = conn.execute(text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """))
    tables = [row[0] for row in result]
    
    print(f"\n📋 Found {len(tables)} tables:")
    for t in tables:
        print(f"  ✓ {t}")
    
    print("\n📊 Row Counts:")
    print("-" * 60)
    for table in tables:
        try:
            count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            print(f"  {table:30} {count:>10,} rows")
        except Exception as e:
            print(f"  {table:30} Error: {e}")
    
    # Check specific table for orders
    print("\n🔍 Checking for orders data:")
    print("-" * 60)
    
    if 'fact_orders' in tables:
        sample = conn.execute(text("""
            SELECT order_id, customer_id, order_status, order_total_cents 
            FROM fact_orders 
            LIMIT 5
        """))
        print("\nSample orders:")
        for row in sample:
            print(f"  Order: {row[0][:20]}... | Customer: {row[1][:20]}... | Status: {row[2]} | Total: R${row[3]/100:.2f}")
    
    print("\n" + "=" * 60)
    print("✅ Database check complete!")
