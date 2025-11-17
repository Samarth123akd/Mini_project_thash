"""Script: load processed CSV into Postgres using DATABASE_URL env var.

Usage: run in repo root where DATA/processed/orders_processed.csv exists.
"""
import os
from etl import load

DB = os.environ.get('DATABASE_URL')
if not DB:
    print('DATABASE_URL not set; nothing to do')
    raise SystemExit(1)

processed = os.path.join('data', 'processed', 'orders_processed.csv')
if not os.path.exists(processed):
    print('Processed CSV not found:', processed)
    raise SystemExit(2)

print('Loading', processed, 'to', DB)
load.load_processed_to('orders', DB, processed)
print('Done')
