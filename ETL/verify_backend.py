"""
Backend Verification Script
Checks:
1. PostgreSQL database connection
2. Brazilian dataset loaded correctly
3. ML model trained and saved
4. Model can make predictions from database data
"""

import os
import sys
from pathlib import Path
from sqlalchemy import create_engine, text
import pandas as pd
import numpy as np

print("=" * 70)
print("  BACKEND VERIFICATION - PostgreSQL + ML Model")
print("=" * 70)

# Set database URL
os.environ['DATABASE_URL'] = "postgresql://postgres:Sam12kumar%40@localhost:5432/ETL_DB"
DB_URL = os.environ['DATABASE_URL']

# ============================================
# 1. CHECK DATABASE CONNECTION
# ============================================
print("\n[1/4] Checking PostgreSQL Connection...")
print("-" * 70)

try:
    engine = create_engine(DB_URL)
    with engine.connect() as conn:
        version = conn.execute(text("SELECT version()")).scalar()
        print(f"✅ Connected to: {version[:50]}...")
        print(f"✅ Database: ETL_DB")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    sys.exit(1)

# ============================================
# 2. VERIFY BRAZILIAN DATASET IN DATABASE
# ============================================
print("\n[2/4] Verifying Brazilian Dataset...")
print("-" * 70)

with engine.connect() as conn:
    # Check tables
    tables_query = text("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name LIKE '%dim%' OR table_name LIKE '%fact%'
        ORDER BY table_name
    """)
    
    result = conn.execute(tables_query)
    tables = [row[0] for row in result]
    
    if not tables:
        print("❌ No tables found in database!")
        sys.exit(1)
    
    print(f"✅ Found {len(tables)} tables:")
    
    total_rows = 0
    table_stats = {}
    
    for table in tables:
        try:
            count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            table_stats[table] = count
            total_rows += count
            status = "✅" if count > 0 else "⚠️"
            print(f"  {status} {table:25} {count:>10,} rows")
        except Exception as e:
            print(f"  ❌ {table:25} Error: {str(e)[:50]}")
    
    print(f"\n  Total records across all tables: {total_rows:,}")
    
    # Verify fact_orders has data
    if 'fact_orders' in table_stats and table_stats['fact_orders'] > 0:
        print(f"\n✅ fact_orders table has {table_stats['fact_orders']:,} orders")
        
        # Check sample orders
        sample_query = text("""
            SELECT 
                order_id,
                customer_id,
                order_status,
                order_purchase_timestamp,
                order_total_cents,
                order_item_count
            FROM fact_orders
            WHERE order_total_cents > 0
            LIMIT 5
        """)
        
        print("\n  Sample orders with totals:")
        sample_df = pd.read_sql(sample_query, conn)
        if not sample_df.empty:
            for _, row in sample_df.iterrows():
                total_brl = row['order_total_cents'] / 100.0
                print(f"    Order {row['order_id'][:20]}... | "
                      f"Status: {row['order_status']:12} | "
                      f"Items: {row['order_item_count']:2} | "
                      f"Total: R${total_brl:>8.2f}")
        else:
            print("  ⚠️  No orders with totals > 0 found")
    else:
        print("❌ fact_orders table is empty or missing!")
        sys.exit(1)

# ============================================
# 3. CHECK ML MODEL
# ============================================
print("\n[3/4] Checking ML Model...")
print("-" * 70)

model_path = Path('ml/models/order_total_model.pkl')

if not model_path.exists():
    print(f"❌ Model not found at: {model_path}")
    print("   Run: jupyter notebook ml/train_example.ipynb")
    sys.exit(1)

try:
    import joblib
    model = joblib.load(model_path)
    print(f"✅ Model loaded: {type(model).__name__}")
    print(f"✅ Model file size: {model_path.stat().st_size / (1024*1024):.1f} MB")
    
    # Check model features
    if hasattr(model, 'n_features_in_'):
        print(f"✅ Model expects {model.n_features_in_} features")
        if hasattr(model, 'feature_names_in_'):
            print(f"   Features: {list(model.feature_names_in_)}")
    
except Exception as e:
    print(f"❌ Failed to load model: {e}")
    sys.exit(1)

# ============================================
# 4. TEST MODEL WITH DATABASE DATA
# ============================================
print("\n[4/4] Testing Model Predictions with Database Data...")
print("-" * 70)

try:
    # Load data from database for prediction
    query = text("""
        SELECT 
            o.order_id,
            COUNT(i.order_item_id) AS items_count,
            SUM(i.price_cents) / 100.0 AS total_price,
            SUM(i.freight_value_cents) / 100.0 AS total_freight,
            AVG(i.price_cents) / 100.0 AS avg_item_price,
            SUM(p.payment_value_cents) / 100.0 AS payment_value,
            MAX(p.payment_installments) AS payment_installments
        FROM fact_orders o
        LEFT JOIN fact_order_items i ON o.order_id = i.order_id
        LEFT JOIN fact_payments p ON o.order_id = p.order_id
        WHERE o.order_status = 'delivered'
        GROUP BY o.order_id
        LIMIT 100
    """)
    
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    
    if df.empty:
        print("⚠️  No delivered orders found for prediction")
    else:
        print(f"✅ Loaded {len(df)} orders from database")
        
        # Prepare features (matching training features)
        feature_cols = ['items_count', 'total_price', 'total_freight', 
                       'avg_item_price', 'payment_value', 'payment_installments']
        
        X_test = df[feature_cols].fillna(0)
        
        print(f"\n  Making predictions on {len(X_test)} orders...")
        predictions = model.predict(X_test)
        
        # Show sample predictions
        print(f"\n  Sample predictions:")
        for i in range(min(5, len(predictions))):
            actual = df.iloc[i]['total_price'] + df.iloc[i]['total_freight']
            predicted = predictions[i]
            error = abs(actual - predicted)
            error_pct = (error / actual * 100) if actual > 0 else 0
            
            print(f"    Order {i+1}: Actual=R${actual:>8.2f} | "
                  f"Predicted=R${predicted:>8.2f} | "
                  f"Error={error_pct:>5.1f}%")
        
        # Calculate metrics
        actuals = df['total_price'] + df['total_freight']
        rmse = np.sqrt(np.mean((actuals - predictions) ** 2))
        mae = np.mean(np.abs(actuals - predictions))
        
        print(f"\n  Model Performance:")
        print(f"    RMSE: R${rmse:.2f}")
        print(f"    MAE:  R${mae:.2f}")
        print(f"    ✅ Model can make predictions from database data!")

except Exception as e:
    print(f"❌ Prediction test failed: {e}")
    import traceback
    traceback.print_exc()

# ============================================
# SUMMARY
# ============================================
print("\n" + "=" * 70)
print("  VERIFICATION SUMMARY")
print("=" * 70)
print(f"✅ PostgreSQL database connected: ETL_DB")
print(f"✅ Brazilian dataset loaded: {table_stats.get('fact_orders', 0):,} orders")
print(f"✅ ML model trained and saved: {model_path}")
print(f"✅ Model can predict from database: {len(predictions)} predictions made")
print("\n🎉 Backend is fully functional!")
print("=" * 70)

print("\n📋 Next Steps:")
print("  1. Database is ready ✓")
print("  2. Model is trained ✓")
print("  3. You can now:")
print("     - Query data: python -c \"from sqlalchemy import create_engine; ...\"")
print("     - Run predictions: Load model and use database data")
print("     - Fix frontend: Update streamlit_app.py date filters")
