"""Aggregate Olist order items into per-order totals and produce a processed CSV.

Produces: data/processed/orders_processed.csv with fields:
- all original order columns (from staging/orders.csv)
- item_count: number of items
- total_amount: sum of price per order (float)
- customer_lifetime_value: CLV calculation per customer
- avg_order_value: average order value per customer
- order_frequency: number of orders per customer

This script is defensive and uses CSV module so it runs without extra deps.
"""
from pathlib import Path
import csv
from datetime import datetime
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
STAGING = ROOT / 'data' / 'staging'
PROCESSED = ROOT / 'data' / 'processed'
PROCESSED.mkdir(parents=True, exist_ok=True)

# Prefer the Olist orders dataset filename when available (brazilian dataset)
olist_orders = list(STAGING.glob('olist_orders*.csv'))
if olist_orders:
    orders_path = olist_orders[0]
else:
    orders_path = STAGING / 'orders.csv'
# order items filename may vary; look for a file starting with olist_order_items
order_items_candidates = list(STAGING.glob('olist_order_items*.csv')) + list(STAGING.glob('order_items*.csv'))
if order_items_candidates:
    order_items_path = order_items_candidates[0]
else:
    # also check Downloads folder as fallback
    dl = Path.home() / 'Downloads' / 'brazilian dataset'
    items = list(dl.glob('olist_order_items*.csv')) + list(dl.glob('order_items*.csv'))
    if items:
        order_items_path = items[0]
    else:
        raise SystemExit(f'order_items CSV not found in staging or Downloads ({STAGING}, {dl})')

print('Using orders:', orders_path)
print('Using order items:', order_items_path)

# Read orders into dict by order_id
orders = {}
with orders_path.open(newline='', encoding='utf-8') as fh:
    reader = csv.DictReader(fh)
    orders_fieldnames = reader.fieldnames or []
    for r in reader:
        orders[r['order_id']] = dict(r)

# Aggregate items
totals = {}
counts = {}
with order_items_path.open(newline='', encoding='utf-8') as fh:
    reader = csv.DictReader(fh)
    for r in reader:
        oid = r.get('order_id')
        if not oid:
            continue
        # price column may be 'price' or 'item_price'
        price_s = r.get('price') or r.get('item_price') or r.get('unit_price') or '0'
        qty_s = r.get('quantity') or r.get('order_item_id') or '1'
        try:
            price = float(price_s) if price_s not in (None, '') else 0.0
        except Exception:
            price = 0.0
        try:
            qty = int(float(qty_s)) if qty_s not in (None, '') else 1
        except Exception:
            qty = 1
        totals[oid] = totals.get(oid, 0.0) + price * qty
        counts[oid] = counts.get(oid, 0) + qty

# Calculate Customer Lifetime Value (CLV) and related metrics
customer_metrics = defaultdict(lambda: {
    'total_spent': 0.0,
    'order_count': 0,
    'order_dates': []
})

for oid, order_data in orders.items():
    customer_id = order_data.get('customer_id')
    if not customer_id:
        continue
    
    order_total = totals.get(oid, 0.0)
    customer_metrics[customer_id]['total_spent'] += order_total
    customer_metrics[customer_id]['order_count'] += 1
    
    # Track order dates for frequency calculation
    order_date = order_data.get('order_purchase_timestamp')
    if order_date:
        customer_metrics[customer_id]['order_dates'].append(order_date)

# Compute derived customer metrics
for customer_id, metrics in customer_metrics.items():
    # Average Order Value
    metrics['avg_order_value'] = metrics['total_spent'] / max(metrics['order_count'], 1)
    
    # Order frequency (orders per month)
    if len(metrics['order_dates']) > 1:
        try:
            dates = sorted([datetime.fromisoformat(d.replace(' ', 'T')) if ' ' in d else datetime.fromisoformat(d) 
                          for d in metrics['order_dates'] if d])
            if len(dates) > 1:
                time_span_days = (dates[-1] - dates[0]).days
                time_span_months = max(time_span_days / 30.0, 1.0)
                metrics['order_frequency'] = metrics['order_count'] / time_span_months
            else:
                metrics['order_frequency'] = metrics['order_count']
        except Exception:
            metrics['order_frequency'] = metrics['order_count']
    else:
        metrics['order_frequency'] = metrics['order_count']
    
    # Customer Lifetime Value (CLV) - simplified formula:
    # CLV = Average Order Value * Order Frequency * Average Customer Lifespan
    # Using a standard assumption of 3 years lifespan
    avg_lifespan_months = 36
    metrics['customer_lifetime_value'] = (
        metrics['avg_order_value'] * 
        metrics['order_frequency'] * 
        avg_lifespan_months
    )

# Compose processed rows
out_path = PROCESSED / 'orders_processed.csv'
fieldnames = list(dict.fromkeys(list(orders_fieldnames) + [
    'item_count', 'total_amount', 'customer_lifetime_value', 
    'avg_order_value', 'order_frequency'
]))
with out_path.open('w', newline='', encoding='utf-8') as fh:
    writer = csv.DictWriter(fh, fieldnames=fieldnames)
    writer.writeheader()
    for oid, o in orders.items():
        row = dict(o)
        row['item_count'] = counts.get(oid, 0)
        row['total_amount'] = f"{totals.get(oid, 0.0):.2f}"
        
        # Add customer metrics
        customer_id = o.get('customer_id')
        if customer_id and customer_id in customer_metrics:
            metrics = customer_metrics[customer_id]
            row['customer_lifetime_value'] = f"{metrics['customer_lifetime_value']:.2f}"
            row['avg_order_value'] = f"{metrics['avg_order_value']:.2f}"
            row['order_frequency'] = f"{metrics['order_frequency']:.2f}"
        else:
            # Defaults if customer metrics unavailable
            row['customer_lifetime_value'] = row['total_amount']
            row['avg_order_value'] = row['total_amount']
            row['order_frequency'] = "1.00"
        
        writer.writerow(row)

print('Wrote', out_path, 'rows=', len(orders))
print('Computed CLV for', len(customer_metrics), 'customers')
