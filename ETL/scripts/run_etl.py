"""Run the full local ETL flow: ingest (CSV), transform, aggregate, and load to DB.

This script is intended for Render Cron Jobs or local testing. It reads
`DATABASE_URL` from the environment to load into Postgres. If not present it
only runs ingestion/transform and writes processed CSVs.
"""
import os
import sys

from etl import transform, load

# simple ingest: expects staging/orders.csv to already exist
# Prefer the Olist/Brazilian dataset filenames when present in staging.
olist_orders = os.path.join('data', 'staging', 'olist_orders_dataset.csv')
default_orders = os.path.join('data', 'staging', 'orders.csv')
IN_PATH = olist_orders if os.path.exists(olist_orders) else default_orders
OUT_PATH = os.path.join('data', 'processed', 'orders_processed.csv')

if not os.path.exists(IN_PATH):
    print('Staging orders not found at', IN_PATH)
    sys.exit(2)

print('Transforming', IN_PATH, '->', OUT_PATH)
transform.transform_csv(IN_PATH, OUT_PATH)

# If an aggregation script exists to combine order_items, call it if present
agg = os.path.join('scripts', 'aggregate_orders.py')
if os.path.exists(agg):
    print('Running aggregation to compute totals')
    # run it as a module
    import runpy
    runpy.run_path(agg, run_name='__main__')

# Load to DB if DATABASE_URL is present
db = os.environ.get('DATABASE_URL')
if db:
    print('Loading processed data to DB')
    load.load_processed_to('orders', db, OUT_PATH)
else:
    print('DATABASE_URL not set; skipping DB load')

print('ETL flow complete')
