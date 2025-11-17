#!/usr/bin/env python3
"""
Load Brazilian E-commerce (Olist) dataset into PostgreSQL.

This script:
1. Reads all CSV files from 'brazilian dataset' folder
2. Loads them into PostgreSQL following the star schema
3. Handles dimension tables first, then fact tables
4. Uses efficient COPY loading for performance

Usage:
    $env:DATABASE_URL = "postgresql://user:pass@localhost:5432/etl_db"
    python scripts/load_brazilian_data.py
"""

import os
import sys
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def get_database_url():
    """Get DATABASE_URL from environment."""
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        print("❌ ERROR: DATABASE_URL environment variable not set")
        print("\nSet it with:")
        print('  $env:DATABASE_URL = "postgresql://user:pass@localhost:5432/etl_db"')
        sys.exit(1)
    return db_url

def find_dataset_folder():
    """Locate the 'brazilian dataset' folder."""
    candidates = [
        Path('brazilian dataset'),
        Path('../brazilian dataset'),
        Path('../../brazilian dataset'),
    ]
    
    for path in candidates:
        if path.exists() and path.is_dir():
            return path
    
    print("❌ ERROR: Could not find 'brazilian dataset' folder")
    print("\nSearched in:")
    for p in candidates:
        print(f"  - {p.absolute()}")
    sys.exit(1)

def load_customers(engine, dataset_path):
    """Load customers dimension table."""
    print("\n📦 Loading dim_customers...")
    
    csv_path = dataset_path / 'olist_customers_dataset.csv'
    if not csv_path.exists():
        print(f"⚠️  Skipping customers (file not found)")
        return
    
    df = pd.read_csv(csv_path)
    print(f"   Read {len(df):,} customer records")
    
    # Map columns to schema
    df_clean = df[[
        'customer_id',
        'customer_unique_id',
        'customer_zip_code_prefix',
        'customer_city',
        'customer_state'
    ]].copy()
    
    # Load to database (upsert on conflict)
    with engine.connect() as conn:
        # Use temporary staging table for better performance
        df_clean.to_sql('_temp_customers', conn, if_exists='replace', index=False)
        
        # Upsert into dim_customers
        conn.execute(text("""
            INSERT INTO dim_customers (
                customer_id, customer_unique_id, customer_zip_code_prefix,
                customer_city, customer_state
            )
            SELECT 
                customer_id, customer_unique_id, customer_zip_code_prefix,
                customer_city, customer_state
            FROM _temp_customers
            ON CONFLICT (customer_id) DO UPDATE SET
                customer_unique_id = EXCLUDED.customer_unique_id,
                customer_zip_code_prefix = EXCLUDED.customer_zip_code_prefix,
                customer_city = EXCLUDED.customer_city,
                customer_state = EXCLUDED.customer_state,
                updated_at = NOW()
        """))
        
        conn.execute(text("DROP TABLE _temp_customers"))
        conn.commit()
    
    print(f"   ✅ Loaded {len(df_clean):,} customers")

def load_products(engine, dataset_path):
    """Load products dimension table."""
    print("\n📦 Loading dim_products...")
    
    csv_path = dataset_path / 'olist_products_dataset.csv'
    if not csv_path.exists():
        print(f"⚠️  Skipping products (file not found)")
        return
    
    df = pd.read_csv(csv_path)
    print(f"   Read {len(df):,} product records")
    
    # Map columns to schema
    df_clean = df[[
        'product_id',
        'product_category_name',
        'product_name_lenght',  # Note: typo in original dataset
        'product_description_lenght',
        'product_photos_qty',
        'product_weight_g',
        'product_length_cm',
        'product_height_cm',
        'product_width_cm'
    ]].copy()
    
    # Rename columns to match schema
    df_clean.columns = [
        'product_id',
        'product_category_name',
        'product_name_length',
        'product_description_length',
        'product_photos_qty',
        'product_weight_g',
        'product_length_cm',
        'product_height_cm',
        'product_width_cm'
    ]
    
    # Load to database
    with engine.connect() as conn:
        df_clean.to_sql('_temp_products', conn, if_exists='replace', index=False)
        
        conn.execute(text("""
            INSERT INTO dim_products (
                product_id, product_category_name, product_name_length,
                product_description_length, product_photos_qty,
                product_weight_g, product_length_cm, product_height_cm, product_width_cm
            )
            SELECT * FROM _temp_products
            ON CONFLICT (product_id) DO UPDATE SET
                product_category_name = EXCLUDED.product_category_name,
                product_name_length = EXCLUDED.product_name_length,
                product_description_length = EXCLUDED.product_description_length,
                product_photos_qty = EXCLUDED.product_photos_qty,
                product_weight_g = EXCLUDED.product_weight_g,
                product_length_cm = EXCLUDED.product_length_cm,
                product_height_cm = EXCLUDED.product_height_cm,
                product_width_cm = EXCLUDED.product_width_cm,
                updated_at = NOW()
        """))
        
        conn.execute(text("DROP TABLE _temp_products"))
        conn.commit()
    
    print(f"   ✅ Loaded {len(df_clean):,} products")

def load_sellers(engine, dataset_path):
    """Load sellers dimension table."""
    print("\n📦 Loading dim_sellers...")
    
    csv_path = dataset_path / 'olist_sellers_dataset.csv'
    if not csv_path.exists():
        print(f"⚠️  Skipping sellers (file not found)")
        return
    
    df = pd.read_csv(csv_path)
    print(f"   Read {len(df):,} seller records")
    
    # Map columns to schema
    df_clean = df[[
        'seller_id',
        'seller_zip_code_prefix',
        'seller_city',
        'seller_state'
    ]].copy()
    
    # Load to database
    with engine.connect() as conn:
        df_clean.to_sql('_temp_sellers', conn, if_exists='replace', index=False)
        
        conn.execute(text("""
            INSERT INTO dim_sellers (
                seller_id, seller_zip_code_prefix, seller_city, seller_state
            )
            SELECT * FROM _temp_sellers
            ON CONFLICT (seller_id) DO UPDATE SET
                seller_zip_code_prefix = EXCLUDED.seller_zip_code_prefix,
                seller_city = EXCLUDED.seller_city,
                seller_state = EXCLUDED.seller_state,
                updated_at = NOW()
        """))
        
        conn.execute(text("DROP TABLE _temp_sellers"))
        conn.commit()
    
    print(f"   ✅ Loaded {len(df_clean):,} sellers")

def load_geolocation(engine, dataset_path):
    """Load geolocation dimension table."""
    print("\n📦 Loading dim_geolocation...")
    
    csv_path = dataset_path / 'olist_geolocation_dataset.csv'
    if not csv_path.exists():
        print(f"⚠️  Skipping geolocation (file not found)")
        return
    
    df = pd.read_csv(csv_path)
    print(f"   Read {len(df):,} geolocation records")
    
    # Map columns to schema
    df_clean = df[[
        'geolocation_zip_code_prefix',
        'geolocation_lat',
        'geolocation_lng',
        'geolocation_city',
        'geolocation_state'
    ]].copy()
    
    # Remove duplicates (geolocation has many duplicates)
    df_clean = df_clean.drop_duplicates()
    print(f"   After removing duplicates: {len(df_clean):,} unique records")
    
    # Load to database (append only, no primary key conflict)
    df_clean.to_sql('dim_geolocation', engine, if_exists='append', index=False)
    
    print(f"   ✅ Loaded {len(df_clean):,} geolocation records")

def load_category_translation(engine, dataset_path):
    """Load product category translation dimension table."""
    print("\n📦 Loading dim_product_category_translation...")
    
    csv_path = dataset_path / 'product_category_name_translation.csv'
    if not csv_path.exists():
        print(f"⚠️  Skipping category translation (file not found)")
        return
    
    df = pd.read_csv(csv_path)
    print(f"   Read {len(df):,} category translation records")
    
    # Map columns to schema
    df_clean = df[[
        'product_category_name',
        'product_category_name_english'
    ]].copy()
    
    # Load to database
    with engine.connect() as conn:
        df_clean.to_sql('_temp_categories', conn, if_exists='replace', index=False)
        
        conn.execute(text("""
            INSERT INTO dim_product_category_translation (
                product_category_name, product_category_name_english
            )
            SELECT * FROM _temp_categories
            ON CONFLICT (product_category_name) DO UPDATE SET
                product_category_name_english = EXCLUDED.product_category_name_english
        """))
        
        conn.execute(text("DROP TABLE _temp_categories"))
        conn.commit()
    
    print(f"   ✅ Loaded {len(df_clean):,} category translations")

def load_orders(engine, dataset_path):
    """Load orders fact table."""
    print("\n📦 Loading fact_orders...")
    
    csv_path = dataset_path / 'olist_orders_dataset.csv'
    if not csv_path.exists():
        print(f"⚠️  Skipping orders (file not found)")
        return
    
    df = pd.read_csv(csv_path, parse_dates=[
        'order_purchase_timestamp',
        'order_approved_at',
        'order_delivered_carrier_date',
        'order_delivered_customer_date',
        'order_estimated_delivery_date'
    ])
    print(f"   Read {len(df):,} order records")
    
    # Map columns to schema
    df_clean = df[[
        'order_id',
        'customer_id',
        'order_status',
        'order_purchase_timestamp',
        'order_approved_at',
        'order_delivered_carrier_date',
        'order_delivered_customer_date',
        'order_estimated_delivery_date'
    ]].copy()
    
    # Add default values for computed fields
    df_clean['order_total_cents'] = 0  # Will be updated from order_items
    df_clean['order_item_count'] = 0  # Will be updated from order_items
    df_clean['currency'] = 'BRL'
    df_clean['source'] = 'brazilian_dataset'
    
    # Load to database
    with engine.connect() as conn:
        df_clean.to_sql('_temp_orders', conn, if_exists='replace', index=False)
        
        conn.execute(text("""
            INSERT INTO fact_orders (
                order_id, customer_id, order_status,
                order_purchase_timestamp, order_approved_at,
                order_delivered_carrier_date, order_delivered_customer_date,
                order_estimated_delivery_date,
                order_total_cents, order_item_count, currency, source
            )
            SELECT * FROM _temp_orders
            ON CONFLICT (order_id) DO UPDATE SET
                order_status = EXCLUDED.order_status,
                order_approved_at = EXCLUDED.order_approved_at,
                order_delivered_carrier_date = EXCLUDED.order_delivered_carrier_date,
                order_delivered_customer_date = EXCLUDED.order_delivered_customer_date,
                order_estimated_delivery_date = EXCLUDED.order_estimated_delivery_date
        """))
        
        conn.execute(text("DROP TABLE _temp_orders"))
        conn.commit()
    
    print(f"   ✅ Loaded {len(df_clean):,} orders")
    return len(df_clean)

def load_order_items(engine, dataset_path):
    """Load order items fact table."""
    print("\n📦 Loading fact_order_items...")
    
    csv_path = dataset_path / 'olist_order_items_dataset.csv'
    if not csv_path.exists():
        print(f"⚠️  Skipping order items (file not found)")
        return
    
    df = pd.read_csv(csv_path, parse_dates=['shipping_limit_date'])
    print(f"   Read {len(df):,} order item records")
    
    # Map columns to schema (convert to cents)
    df_clean = df[[
        'order_id',
        'order_item_id',
        'product_id',
        'seller_id',
        'shipping_limit_date',
        'price',
        'freight_value'
    ]].copy()
    
    # Rename and convert to cents
    df_clean.columns = [
        'order_id',
        'order_item_sequence',
        'product_id',
        'seller_id',
        'shipping_limit_date',
        'price',
        'freight_value'
    ]
    
    df_clean['price_cents'] = (df_clean['price'] * 100).fillna(0).astype(int)
    df_clean['freight_value_cents'] = (df_clean['freight_value'] * 100).fillna(0).astype(int)
    df_clean = df_clean.drop(['price', 'freight_value'], axis=1)
    
    # Load to database
    df_clean.to_sql('fact_order_items', engine, if_exists='append', index=False)
    
    print(f"   ✅ Loaded {len(df_clean):,} order items")
    
    # Update order totals in fact_orders
    print("   Updating order totals...")
    with engine.connect() as conn:
        conn.execute(text("""
            UPDATE fact_orders o
            SET 
                order_total_cents = COALESCE(i.total_cents, 0),
                order_item_count = COALESCE(i.item_count, 0)
            FROM (
                SELECT 
                    order_id,
                    SUM(price_cents + freight_value_cents) AS total_cents,
                    COUNT(*) AS item_count
                FROM fact_order_items
                GROUP BY order_id
            ) i
            WHERE o.order_id = i.order_id
        """))
        conn.commit()
    
    print("   ✅ Order totals updated")

def load_payments(engine, dataset_path):
    """Load payments fact table."""
    print("\n📦 Loading fact_payments...")
    
    csv_path = dataset_path / 'olist_order_payments_dataset.csv'
    if not csv_path.exists():
        print(f"⚠️  Skipping payments (file not found)")
        return
    
    df = pd.read_csv(csv_path)
    print(f"   Read {len(df):,} payment records")
    
    # Map columns to schema (convert to cents)
    df_clean = df[[
        'order_id',
        'payment_sequential',
        'payment_type',
        'payment_installments',
        'payment_value'
    ]].copy()
    
    df_clean['payment_value_cents'] = (df_clean['payment_value'] * 100).fillna(0).astype(int)
    df_clean['currency'] = 'BRL'
    df_clean = df_clean.drop(['payment_value'], axis=1)
    
    # Load to database
    df_clean.to_sql('fact_payments', engine, if_exists='append', index=False)
    
    print(f"   ✅ Loaded {len(df_clean):,} payments")

def load_reviews(engine, dataset_path):
    """Load reviews fact table."""
    print("\n📦 Loading fact_reviews...")
    
    csv_path = dataset_path / 'olist_order_reviews_dataset.csv'
    if not csv_path.exists():
        print(f"⚠️  Skipping reviews (file not found)")
        return
    
    df = pd.read_csv(csv_path, parse_dates=[
        'review_creation_date',
        'review_answer_timestamp'
    ])
    print(f"   Read {len(df):,} review records")
    
    # Map columns to schema
    df_clean = df[[
        'review_id',
        'order_id',
        'review_score',
        'review_comment_title',
        'review_comment_message',
        'review_creation_date',
        'review_answer_timestamp'
    ]].copy()
    
    # Load to database
    with engine.connect() as conn:
        df_clean.to_sql('_temp_reviews', conn, if_exists='replace', index=False)
        
        conn.execute(text("""
            INSERT INTO fact_reviews (
                review_id, order_id, review_score,
                review_comment_title, review_comment_message,
                review_creation_date, review_answer_timestamp
            )
            SELECT * FROM _temp_reviews
            ON CONFLICT (review_id) DO UPDATE SET
                review_score = EXCLUDED.review_score,
                review_comment_title = EXCLUDED.review_comment_title,
                review_comment_message = EXCLUDED.review_comment_message,
                review_creation_date = EXCLUDED.review_creation_date,
                review_answer_timestamp = EXCLUDED.review_answer_timestamp
        """))
        
        conn.execute(text("DROP TABLE _temp_reviews"))
        conn.commit()
    
    print(f"   ✅ Loaded {len(df_clean):,} reviews")

def create_audit_record(engine, run_id, total_rows, status='success'):
    """Create audit record for this load."""
    print("\n📝 Creating audit record...")
    
    with engine.connect() as conn:
        conn.execute(text("""
            INSERT INTO ingest_audit (
                run_id, rows_ingested, status, 
                metadata, started_at, finished_at
            ) VALUES (
                :run_id, :rows, :status,
                :metadata, :started, :finished
            )
            ON CONFLICT (run_id) DO UPDATE SET
                rows_ingested = EXCLUDED.rows_ingested,
                status = EXCLUDED.status,
                finished_at = EXCLUDED.finished_at
        """), {
            'run_id': run_id,
            'rows': total_rows,
            'status': status,
            'metadata': '{"source": "brazilian_dataset", "script": "load_brazilian_data.py"}',
            'started': datetime.now().replace(microsecond=0),
            'finished': datetime.now().replace(microsecond=0)
        })
        conn.commit()
    
    print(f"   ✅ Audit record created: {run_id}")

def verify_data(engine):
    """Verify loaded data with row counts."""
    print("\n🔍 Verifying loaded data...\n")
    
    tables = [
        'dim_customers',
        'dim_products',
        'dim_sellers',
        'dim_geolocation',
        'dim_product_category_translation',
        'fact_orders',
        'fact_order_items',
        'fact_payments',
        'fact_reviews'
    ]
    
    with engine.connect() as conn:
        for table in tables:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            count = result.scalar()
            print(f"   {table:25} {count:>10,} rows")

def main():
    """Main execution function."""
    print("=" * 60)
    print("  Brazilian E-commerce Dataset → PostgreSQL Loader")
    print("=" * 60)
    
    # Get database connection
    db_url = get_database_url()
    print(f"\n📊 Database: {db_url.split('@')[-1] if '@' in db_url else 'localhost'}")
    
    # Find dataset folder
    dataset_path = find_dataset_folder()
    print(f"📁 Dataset: {dataset_path.absolute()}")
    
    # Create engine
    try:
        engine = create_engine(db_url)
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure PostgreSQL is running")
        print("2. Verify DATABASE_URL is correct")
        print("3. Check if database exists: psql -l")
        print("4. Create tables first: psql $DATABASE_URL -f sql/schema.sql")
        sys.exit(1)
    
    # Generate run ID
    run_id = f"brazilian_load_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"🔖 Run ID: {run_id}")
    
    try:
        # Load data in order (dimensions first, then facts)
        total_rows = 0
        
        load_customers(engine, dataset_path)
        load_products(engine, dataset_path)
        load_sellers(engine, dataset_path)
        load_geolocation(engine, dataset_path)
        load_category_translation(engine, dataset_path)
        order_count = load_orders(engine, dataset_path)
        load_order_items(engine, dataset_path)
        load_payments(engine, dataset_path)
        load_reviews(engine, dataset_path)
        
        # Create audit record
        create_audit_record(engine, run_id, order_count or 0, 'success')
        
        # Verify data
        verify_data(engine)
        
        print("\n" + "=" * 60)
        print("  ✅ SUCCESS! Brazilian dataset loaded to PostgreSQL")
        print("=" * 60)
        print("\nNext steps:")
        print("  1. Launch dashboard: streamlit run dashboard/streamlit_app.py")
        print("  2. Train ML model: jupyter notebook ml/train_example.ipynb")
        print("  3. Run Airflow DAG: airflow dags trigger etl_pipeline")
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        
        try:
            create_audit_record(engine, run_id, 0, 'failed')
        except:
            pass
        
        sys.exit(1)

if __name__ == '__main__':
    main()
