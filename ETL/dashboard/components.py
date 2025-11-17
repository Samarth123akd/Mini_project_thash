"""Visualization helpers for the dashboard.

Keep this dependency-light. If plotly is available we provide a helper, but
the dashboard can work without it.
"""
from typing import List, Dict
import csv
import os


def top_products(processed_csv: str, top_n: int = 10) -> List[Dict]:
    if not os.path.exists(processed_csv):
        return []
    counts = {}
    with open(processed_csv, newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        for r in reader:
            desc = r.get('Description') or r.get('description') or r.get('StockCode')
            if not desc:
                continue
            counts[desc] = counts.get(desc, 0) + int(float(r.get('quantity') or 0))

    items = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:top_n]
    return [{'product': k, 'quantity': v} for k, v in items]


def top_products_from_staging(staging_dir: str = 'data/staging', top_n: int = 10) -> List[Dict]:
    """Compute top products from staging order_items and products files.

    - looks for an order_items CSV (order_item rows with order_id, product_id, price)
    - looks for a products CSV to map product_id -> product name (best effort)
    Returns list of {'product_id': id, 'product_name': name_or_id, 'quantity': qty}
    """
    staging_dir = os.path.abspath(staging_dir)
    if not os.path.exists(staging_dir):
        return []

    # find order_items file
    order_items_file = None
    for fname in os.listdir(staging_dir):
        if fname.lower().startswith('olist_order_items') or 'order_items' in fname.lower():
            order_items_file = os.path.join(staging_dir, fname)
            break
    if not order_items_file:
        return []

    # find products file (optional)
    products_file = None
    for fname in os.listdir(staging_dir):
        if fname.lower().startswith('olist_product') or 'product' in fname.lower():
            products_file = os.path.join(staging_dir, fname)
            break

    # map product_id -> quantity
    counts = {}
    with open(order_items_file, newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        for r in reader:
            pid = r.get('product_id') or r.get('product_id')
            if not pid:
                continue
            # There is no explicit quantity in olist order_items; treat each row as quantity=1
            qty = 1
            try:
                # some datasets might have a 'quantity' column
                qty = int(float(r.get('quantity') or r.get('order_item_id') or 1))
            except Exception:
                qty = 1
            counts[pid] = counts.get(pid, 0) + qty

    # build product name map if products_file exists
    names = {}
    if products_file and os.path.exists(products_file):
        with open(products_file, newline='', encoding='utf-8') as fh:
            reader = csv.DictReader(fh)
            for r in reader:
                pid = r.get('product_id') or r.get('id')
                if not pid:
                    continue
                name = r.get('product_name') or r.get('product_category_name') or r.get('product_type_name') or r.get('product_name_lenght')
                # fallback to other possible keys
                if not name:
                    for k in r.keys():
                        if 'name' in k.lower():
                            name = r.get(k)
                            break
                if name:
                    names[pid] = name

    items = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:top_n]
    out = []
    for pid, qty in items:
        out.append({'product_id': pid, 'product_name': names.get(pid, pid), 'quantity': qty})
    return out
