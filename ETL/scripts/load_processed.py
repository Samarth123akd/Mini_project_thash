#!/usr/bin/env python3
"""Load processed orders CSV into etl.orders_processed table"""
import os
import sys
import pandas as pd
from sqlalchemy import create_engine

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set")
    sys.exit(1)

print(f"Loading processed orders to {DATABASE_URL}")

# Read CSV
csv_path = os.path.join("data", "processed", "orders_processed.csv")
df = pd.read_csv(csv_path)
print(f"Read {len(df)} rows from {csv_path}")

# Load to database
engine = create_engine(DATABASE_URL)
df.to_sql('orders_processed', con=engine, schema='etl', if_exists='replace', index=False)

print(f"✅ Loaded {len(df)} rows to etl.orders_processed")
