"""Load processed CSV into a local SQLite DB for safe testing.

Creates `data/tmp/orders.db` and a table `orders_sqlite`. All columns are
stored as TEXT to avoid type issues; this is intended for verification only.
"""
import os
import csv
import sqlite3


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
processed = os.path.join(ROOT, 'data', 'processed', 'orders_processed.csv')
out_dir = os.path.join(ROOT, 'data', 'tmp')
os.makedirs(out_dir, exist_ok=True)
db_path = os.path.join(out_dir, 'orders.db')

if not os.path.exists(processed):
    raise SystemExit(f'Processed CSV not found: {processed}')

with open(processed, newline='', encoding='utf-8') as fh:
    reader = csv.DictReader(fh)
    fieldnames = reader.fieldnames or []

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # Drop existing table for a clean load
    cur.execute('DROP TABLE IF EXISTS orders_sqlite')

    # Create table with all TEXT columns
    cols_sql = ', '.join([f'"{c}" TEXT' for c in fieldnames])
    cur.execute(f'CREATE TABLE orders_sqlite ({cols_sql})')

    placeholders = ','.join(['?'] * len(fieldnames))
    insert_sql = f'INSERT INTO orders_sqlite ({",".join([f"\"{c}\"" for c in fieldnames])}) VALUES ({placeholders})'

    batch = []
    batch_size = 1000
    total = 0
    for r in reader:
        row = [r.get(c, '') for c in fieldnames]
        batch.append(row)
        if len(batch) >= batch_size:
            cur.executemany(insert_sql, batch)
            total += len(batch)
            batch = []
    if batch:
        cur.executemany(insert_sql, batch)
        total += len(batch)

    conn.commit()
    cur.execute('SELECT COUNT(*) FROM orders_sqlite')
    cnt = cur.fetchone()[0]
    print('Wrote rows to sqlite db:', db_path)
    print('Row count reported by sqlite:', cnt)

    # print a sample row
    cur.execute('SELECT * FROM orders_sqlite LIMIT 1')
    sample = cur.fetchone()
    if sample:
        print('Sample row (first):')
        print(dict(zip(fieldnames, sample)))

    conn.close()
